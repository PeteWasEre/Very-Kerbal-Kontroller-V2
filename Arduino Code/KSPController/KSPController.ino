#include <Wire.h>
#include "KSPController.h"
#include "utils.h"

/* start code */
void setup() {
  /* setup the digital output pins */
  for (i = c_first_pwm_pin; i <= c_last_pwm_pin; i++) {
    pinMode(i, OUTPUT);
  }

  /* turn on the power light red to start test*/
  digitalWrite(c_power_led_R_pin, HIGH);

  /* setup the digital input pins to activate internal pullup resistors */
  for (i = c_first_input_pin1; i <= c_last_input_pin1; i++) {
    pinMode(i, INPUT_PULLUP);
  }
  for (i = c_first_input_pin2; i <= c_last_input_pin2;
       i++) {
    pinMode(i, INPUT_PULLUP);
  }

  /* set unused analogue input pins as digital outs forced low to prevent noise */
  for (i = A8; i <= A15; i++) {
    pinMode(i, OUTPUT);
    digitalWrite(i, LOW);
  }

  /* wake up the I2C_bus */
  Wire.begin();

  /* check we have all the MCP23017 chips */
  for (byte a = c_first_mux_address; a < c_last_mux_address; a++)   /* chip addresses start at 0x20, max of 8 chips */
  {
    Wire.beginTransmission (a);
    if (Wire.endTransmission () == 0) {
      n_mux_chips_detected++;
    }
  }
  if (n_mux_chips_detected != c_num_mux_chips) {
    sys_error(c_error_code_mux_missing);
  }

  /* setup the MUX output lines - MUX pins default to input on start up */
  mux_Tx(0x23, 0x00, 0x00);  /* MUX 0x23, IODIRA, Set all to output (0) */
  mux_Tx(0x23, 0x01, B11111110);  /* MUX 0x23, IODIRB, Set only pin 1 to output (0) */
  mux_Tx(0x24, 0x00, 0x00);  /* MUX 0x24, IODIRA, Set all to output (0) */
  mux_Tx(0x24, 0x01, B11111110);  /* MUX 0x24, IODIRB, Set only pin 1 to output (0) */

  /* reverse the polarity for all pins except the output lines */
  mux_Tx(0x20, 0x02, 0xFF);     /* Mux 0x20, IPOLA, Set All to reverse */
  mux_Tx(0x20, 0x03, 0xFF);     /* Mux 0x20, IPOLB, Set All to reverse */
  mux_Tx(0x21, 0x02, 0xFF);     /* Mux 0x21, IPOLA, Set All to reverse */
  mux_Tx(0x21, 0x03, 0xFF);     /* Mux 0x21, IPOLB, Set All to reverse */
  mux_Tx(0x22, 0x02, 0xFF);     /* Mux 0x22, IPOLB, Set All to reverse */
  mux_Tx(0x22, 0x03, 0xFF);     /* Mux 0x22, IPOLB, Set All to reverse */
  mux_Tx(0x23, 0x03, B11111110); /* Mux 0x23, IPOLB, Set All but pin B1 (output) to reverse */
  mux_Tx(0x24, 0x03, B11111110); /* Mux 0x23, IPOLB, Set All but pin B1 (output) to reverse */

  /* start serial comms */
  Serial.begin(c_serial_speed);

  /* turn on all the lights during the start up for a BIT check */
  digitalWrite(c_error_led_pin, HIGH);
  digitalWrite(c_overrun_led_pin, HIGH);

  /* Cycle through the other lights */
  digitalWrite(c_sys_light_enable_1, HIGH);
  digitalWrite(c_sys_light_enable_2, HIGH);
  for (i = 0; i < 16; i++) {
    byte a = 0;
    if (i < 8) {
      bitSet(a, i);
      mux_Tx(0x24, 0x12, a);  /* MUX 0x23, GPIOB */
    }
    else if (i == 8) {
      mux_Tx(0x24, 0x12, 0);  /* MUX 0x23, GPIOB */
      mux_Tx(0x24, 0x13, 1);  /* MUX 0x23, GPIOB */
    }
    else {
      mux_Tx(0x24, 0x13, 0);  /* MUX 0x23, GPIOB */
      bitSet(a, i - 9);
      mux_Tx(0x23, 0x12, a);  /* MUX 0x23, GPIOB */
    }
#ifdef DEBUG
    delay(c_light_bit_time_d);
#else
    delay(c_light_bit_time);
#endif
  }
  mux_Tx(0x23, 0x12, 0);  /* MUX 0x23, GPIOB */
  digitalWrite(c_sys_light_enable_1, LOW);
  digitalWrite(c_sys_light_enable_2, LOW);

  /* turn off lights and turn the power light green to show BIT complete */
  digitalWrite(c_power_led_R_pin, LOW);
  analogWrite(c_power_led_G_pin, c_light_brigtness);
  digitalWrite(c_error_led_pin, LOW);
  digitalWrite(c_overrun_led_pin, LOW);
}

/* main code loop */
void loop() {

  /* work out if we are ready for the next frame. As this is real time we need to allow
    for the processing time and run a fixed start delay
  */
  t_current_frame = millis();  /* frame start time */
  t_frame_time = t_current_frame - t_last_frame;  /* time since last frame */
  t_run_time = t_current_frame - t_power_on; /* keep track of time since power on */

  if (t_frame_time >= c_frame_time_target) { /* its time to run */
    t_last_frame = t_current_frame; /* update the last frame time */

    /* check if data received, if so read it in */
    if (Serial.available() == sizeof(x_inputbuffer)) {
      Serial.readBytes(x_inputbuffer, sizeof(x_inputbuffer));
      if (!bitRead(x_inputbuffer[0],0)) {
        f_data_requested = TRUE;
      }
      else if (bitRead(x_inputbuffer[0],0)) {
        f_data_received = TRUE;
      }
      t_last_serial_time = 0;
    }
    else {
      t_last_serial_time += t_frame_time;
    }


#ifdef DEBUG   /* in debug mode ignore serial timeouts, run regardless of python connection */
    if (0) {
#else
    if (t_last_serial_time >= c_serial_timeout) {
#endif
      /* no data from the main program, turn off all the lights and flash the error light */
      digitalWrite(c_sys_light_enable_1, LOW);
      digitalWrite(c_sys_light_enable_2, LOW);
      light_flash_pwm(c_error_led_pin, &t_error_light, &f_error_light_state, c_error_light_flash, c_error_flash_intensity);
    }
    else { /* serial hasn't timed out, proceed as normal */
      f_serial_state = true;

      /* turn off the error light, if it was flashing on when serial started it stays on! */
      digitalWrite(c_error_led_pin, LOW);

      /* re-enable the system lights */
      analogWrite(c_sys_light_enable_1, c_light_brigtness);
      analogWrite(c_sys_light_enable_2, c_light_brigtness);

      /* set the status byte */
      x_databuffer[0] = B00000001; /* bit 1 is true when alive */

      /* read all the inputs into the databuffer */
      read_inputs(&x_databuffer[1]);

#ifdef DEBUG   /* Print all the inputs to serial. */
      for (i = 0; i < 10; i++) {
        printBits(x_databuffer[i]);
        Serial.print(" ");
      }
      for (i = 10; i < 17; i++) {
        Serial.print(x_databuffer[i]);
        Serial.print(" ");
      }
#endif

      /* write the outputs to the lights  */
#ifdef DEBUG /* in debug mode work regardless of serial */
      if (1) {
#else
      if (f_data_received) {
#endif
        write_outputs(x_inputbuffer, x_databuffer);
        f_data_received = FALSE;
      }

      /* check for high temp */
      if (x_databuffer[10] > c_temp_max) {
        sys_error(c_overtemp_error_code);
      }

    }
    /* measure the processing time, signal if an overun occurs. add actual frame time to data buffer */
    t_frame_actual = millis() - t_current_frame;
    x_databuffer[18] = t_frame_actual;

#ifdef DEBUG
    Serial.println(t_frame_actual);
#endif

    if (t_frame_actual >= c_frame_time_target) {
      digitalWrite(c_overrun_led_pin, HIGH);
    }
    else {
      digitalWrite(c_overrun_led_pin, LOW);
    }

    /* if data was requested, send data back */
    if (f_data_requested) {
      Serial.write(x_databuffer, sizeof(x_databuffer));
      f_data_requested = FALSE;
    }
  } /* end of 'if frame time reached' condition */
}

int read_inputs(byte buff[]) {
  /* this function reads in all digital inputs and places them in the data buffer */
  /* NOTE: all locations in the buffer are offset by 1 to the left! aka 0 here is 1 in the main function */

  /* read and map in the direct digital IO pins */
  for (i = c_first_input_pin1; i <= c_last_input_pin1; i++) {
    bitWrite(buff[0], (i - c_first_input_pin1), !digitalRead(i));
  }
  for (i = c_first_input_pin2; i <= c_last_input_pin2; i++) {
    bitWrite(buff[0], (i - c_first_input_pin2 + c_last_input_pin1 - 1), !digitalRead(i));
  }

  /* now read the digital ins from each MUX bank.
      note that they already come as bytes so they can be copied straight in.
  */
  mux_Rx(0x20, 0x12, 1, &buff[1]);
  mux_Rx(0x20, 0x13, 1, &buff[2]);
  mux_Rx(0x21, 0x12, 1, &buff[3]);
  mux_Rx(0x21, 0x13, 1, &buff[4]);
  mux_Rx(0x22, 0x12, 1, &buff[5]);
  mux_Rx(0x22, 0x13, 1, &buff[6]);
  mux_Rx(0x23, 0x13, 1, &buff[7]);
  mux_Rx(0x24, 0x13, 1, &buff[8]);

  /* read the analog inputs and map to a byte */
  buff[9] = map(analogRead(A0), 0, 1023, 0, 255); /* Temperature Sensor */
  buff[10] = map(analogRead(A4), 0, 1023, 0, 255); /* Rotation X */
  buff[11] = map(analogRead(A5), 0, 1023, 0, 255); /* Rotation Y */
  buff[12] = map(analogRead(A6), 0, 1023, 0, 255); /* Rotation Z */
  buff[13] = map(analogRead(A1), 0, 1023, 255, 0); /* Translation X  - REVERSED*/
  buff[14] = map(analogRead(A2), 0, 1023, 255, 0); /* Translation Y  - REVERSED*/
  buff[15] = map(analogRead(A3), 0, 1023, 0, 255); /* Translation Z */
  buff[16] = map(analogRead(A7), 0, 1023, 0, 255); /* Throttle */
  return 0;
}

int write_outputs(byte inputs[], byte outputs[]) {
  byte temp = 0;
  bitWrite(temp, 0, bitRead(outputs[3], 3)); /* RCS*/
  bitWrite(temp, 1, bitRead(outputs[4], 6)); /* Lights */
  bitWrite(temp, 2, bitRead(inputs[0], 2)); /* Gear Green */

  if (!bitRead(inputs[0], 1) && !bitRead(inputs[0], 2)) {
    bitWrite(temp, 3, int(millis()/ c_gear_light_flash) % 2); /* Gear Red */
  }
  else {
    bitWrite(temp, 3, 0); /* Gear Red */
  }
  bitWrite(temp, 4, bitRead(outputs[3], 2)); /* NWS*/
  bitWrite(temp, 5, bitRead(outputs[3], 1)); /* park brake */
  bitWrite(temp, 6, (bitRead(outputs[4], 2) && !bitRead(outputs[3], 1))); /* Brakes, but not park brake*/
  /* bit 7 not used */
  mux_Tx(0x23, 0x12, temp);  /* MUX 0x23, GPIOA */

  /* MUX 23 bank B output not used */

  temp = 0;

  if (bitRead(outputs[5], 4)) { /* Throttle 100% */
    bitSet(temp, 1);
  }
  else if (bitRead(outputs[5], 5) || bitRead(outputs[5], 6) || bitRead(outputs[5], 7)) { /* Throttle Limited */
    bitSet(temp, 2);
  }
  else { /* Throttle Off */
    bitSet(temp, 0);
  }

  if (bitRead(outputs[5], 0) || bitRead(outputs[5], 1) || bitRead(outputs[5], 2) || bitRead(outputs[5], 3)) { /* Controls On */
    if (bitRead(outputs[4], 0)) { /* Controls Fine */
      bitSet(temp, 5);
    }
    else { /* Controls Normal */
      bitSet(temp, 4);
    }
  }
  else { /* Controls Off */
    bitSet(temp, 3);
  }

  if (bitRead(outputs[3], 4) && !bitRead(inputs[0],3)) { /* SAS ON but not override */
    bitSet(temp, 7);
  }
  else if (!bitRead(outputs[3], 4)) { /* SAS ON but not override */
    bitSet(temp, 6);
  }
   
  mux_Tx(0x24, 0x12, temp);  /* MUX 0x24, GPIOA */

  temp = 0; 
  bitWrite(temp, 0, (bitRead(outputs[3], 4) && bitRead(inputs[0],3))); /* SAS Overide and SAS ON*/
  mux_Tx(0x24, 0x13, temp);  /* MUX 0x24, GPIOB */
}


