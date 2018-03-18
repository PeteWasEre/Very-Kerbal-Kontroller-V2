#include <Wire.h>
#include <LiquidCrystal.h>
#include "KSPController.h"
#include "utils.h"

/* start code */
void setup() {
  /* set the PWM frequency on pin 6 to avoid fan whine */
  TCCR4B &= ~(B00000111);   /* set the three bits in TCCR2B to 0 */
  TCCR4B |= B00000001;      /* set the last three bits in TCCR4B with our new value, 1 is max freq */

  /* setup the digital output pins */
  for (i = c_first_pwm_pin; i <= c_last_pwm_pin; i++) {
    pinMode(i, OUTPUT);
  }
  for (i = c_first_output_pin; i <= c_last_output_pin; i++) {
    pinMode(i, OUTPUT);
  }

  /* turn on all the lights during the start up for a BIT check */
  digitalWrite(c_power_led_pin, HIGH);
  digitalWrite(c_error_led_pin, HIGH);
  digitalWrite(c_overrun_led_pin, HIGH);
  analogWrite(c_ap_reset_pin, 255);
  analogWrite(c_ap_power_pin, 255);

  /* setup the digital input pins to activate internal pullup resistors */
  for (i = c_first_input_pin1; i <= c_last_input_pin1; i++) {
    pinMode(i, INPUT_PULLUP);
  }
  for (i = c_first_input_pin2; i <= c_last_input_pin2; i++) {
    pinMode(i, INPUT_PULLUP);
  }

  /* set unused analogue input pins as digital outs forced low to prevent noise */
  for (i = A10; i <= A15; i++) {
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

  /* reverse the polarity for all pins except the stage switch (which is already reversed) */
  mux_Tx(0x20, 0x02, 0xFF);     /* Mux 0x20, IPOLA, Set All to reverse */
  mux_Tx(0x20, 0x03, B01111111); /* Mux 0x20, IPOLB, Set All but pin B7 (stage sw) to reverse */
  mux_Tx(0x21, 0x02, 0xFF);     /* Mux 0x21, IPOLA, Set All to reverse */
  mux_Tx(0x21, 0x03, 0xFF);     /* Mux 0x21, IPOLB, Set All to reverse */
  mux_Tx(0x22, 0x03, 0xFF);     /* Mux 0x22, IPOLB, Set All to reverse */
  mux_Tx(0x23, 0x03, B11111110); /* Mux 0x23, IPOLB, Set All but pin B1 (output) to reverse */
  mux_Tx(0x24, 0x03, B11111110); /* Mux 0x23, IPOLB, Set All but pin B1 (output) to reverse */
  mux_Tx(0x25, 0x02, 0xFF);     /* Mux 0x25, IPOLA, Set All to reverse */
  mux_Tx(0x25, 0x03, 0xFF);     /* Mux 0x25, IPOLB, Set All to reverse */
  mux_Tx(0x26, 0x02, 0xFF);     /* Mux 0x26, IPOLA, Set All to reverse */
  mux_Tx(0x26, 0x03, 0xFF);     /* Mux 0x27, IPOLB, Set All to reverse */

  /* turn on the input pullups on the AP panel */
  mux_Tx(0x25, 0x0C, 0xFF);     /* Mux 0x25, GPPUA, Set All to pullup */
  mux_Tx(0x25, 0x0D, 0xFF);     /* Mux 0x25, GPPUB, Set All to pullup */
  mux_Tx(0x26, 0x0C, 0xFF);     /* Mux 0x26, GPPUA, Set All to pullup */
  mux_Tx(0x26, 0x0D, 0xFF);     /* Mux 0x26, GPPUB, Set All to pullup */

  /* start serial comms */
  Serial.begin(c_serial_speed);

  /* hold to allow light BIT to be seen */
  delay(c_light_bit_time);
  digitalWrite(c_power_led_pin, LOW);
  digitalWrite(c_error_led_pin, LOW);
  digitalWrite(c_overrun_led_pin, LOW);
  analogWrite(c_ap_reset_pin, 0);
  analogWrite(c_ap_power_pin, 0);
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
    t_last_frame = t_current_frame;

    /* check if data received, if so read it in */
    if (Serial.available() == sizeof(x_inputbuffer)) {
      Serial.readBytes(x_inputbuffer, sizeof(x_inputbuffer));
      if (x_inputbuffer[0] == 0x00) {
        f_data_requested = TRUE;
      }
      else if (x_inputbuffer[0] == 0x01) {
        f_data_received = TRUE;
      }
      t_last_serial_time = 0;
    }
    else {
      t_last_serial_time += t_frame_time;
    }

    /* DEBUG - Removes requirement for a valid serial connection, allowing testing without game running */
    #ifdef DEBUG
    t_last_serial_time = 0;
    #endif
    
    /* check the input power */
    if (analogRead(A0) < c_voltage_threshold) {
      /* powered by USB only, flash the power light and do nothing else */
      light_flash_pwm(c_power_led_pin, &t_power_light, &f_power_light_state, c_power_light_flash, 10);
      /* turn off lights */
      digitalWrite(c_error_led_pin, LOW);
      digitalWrite(c_dimmer_pwm_pin, LOW);
      digitalWrite(c_ap_power_pin, LOW);
      digitalWrite(c_ap_dimmer_pin, LOW);
      digitalWrite(c_ap_reset_pin, LOW);
      
      f_power_on_first_pass = TRUE;
      t_run_time = 0;
      x_databuffer[0] = B00000001; /* set the status byte to 1 to alive (bit 1) but unpowered (bit 2)*/
    }
    else { /* power is on, run the main program */
      if (f_power_on_first_pass ) {
        t_power_on = t_current_frame;
        f_power_on_first_pass = FALSE;
      }
      /* Manage the dimmer input  */
      
      x_dimmer_setting = map(analogRead(A2), 0, 1023, 255, 2); /* Dimmer - REVERSED - set a minimum to avoid no lights */
      /* Turn on the power light */
      light_dim_ctl(c_power_led_pin, true, x_dimmer_setting, 0);

      if (t_last_serial_time >= c_serial_timeout) {
        /* no data from the main program, turn off all the lights and flash the error light */
        mux_Tx(0x23, 0x12, 0x00);  /* MUX 0x23, GPIOA */
        mux_Tx(0x23, 0x13, 0x00);  /* MUX 0x23, GPIOB */
        mux_Tx(0x24, 0x12, 0x00);  /* MUX 0x24, GPIOA */
        mux_Tx(0x24, 0x13, 0x00);  /* MUX 0x24, GPIOB */
        light_flash_pwm(c_error_led_pin, &t_error_light, &f_error_light_state, c_error_light_flash, x_dimmer_setting);
        f_serial_state = false;
      }
      else { /* serial hasn't timed out, proceed as normal */
        f_serial_state = true;

        /* turn off the error light, if it was flashing on when serial started it stays on! */
        digitalWrite(c_error_led_pin, LOW);

        /* set the status byte */
        x_databuffer[0] = B00000011; /* bit 1 is true (alive) and bit 2 is true (powered) */

        /* read all the inputs into the databuffer */
        read_inputs(&x_databuffer[1]);

        /* write the outputs to the lights  */
        if (f_data_received) {
          write_outputs(x_inputbuffer, x_databuffer);
          f_data_received = FALSE;
        }

        /* manage the autopilot */
        n_ap_subband_count = (n_ap_subband_count + 1) % c_ap_subband;
        if (n_ap_subband_count == 0){
          autopilot(x_databuffer);
        }
      }
      /* manage dimmer controls */
      light_dim_ctl(c_dimmer_pwm_pin, f_serial_state, x_dimmer_setting, 0);
      light_dim_ctl(c_ap_power_pin, f_serial_state, x_dimmer_setting, 0);
      light_dim_ctl(c_ap_dimmer_pin, f_ap_power_state, x_dimmer_setting, 0);
      light_dim_ctl(c_ap_reset_pin, f_ap_power_state, x_dimmer_setting, 0);

      /* manage the fan */
      if (t_run_time < c_fan_power_up_time) { /* max speed initially to ensure it starts */
        x_fan_speed = 255;
      }
      else { /* map fan speed to temp v fan speed curve */
        x_fan_speed = int(x_databuffer[18] * c_fan_speed_m + c_fan_speed_b);
      }
      analogWrite(c_fan_pwm_pin, x_fan_speed);

      /* check for high temp */
      if (x_databuffer[18] > c_temp_max) {
        sys_error(c_overtemp_error_code);
      }

      /* measure the processing time, signal if an overun occurs. add actual frame time to data buffer */
      t_frame_actual = millis() - t_current_frame;
      x_databuffer[27] = t_frame_actual;

      if (t_frame_actual >= c_frame_time_target) {
        digitalWrite(c_overrun_led_pin, HIGH);
        #ifdef DEBUG
        Serial.println(t_frame_actual);
        #endif
      }
      else {
        digitalWrite(c_overrun_led_pin, LOW);
      }

      /* add the fan speed data to the buffer */
      x_databuffer[28] = x_fan_speed;

      /* if data was requested, send data back */
      if (f_data_requested) {
        Serial.write(x_databuffer, sizeof(x_databuffer));
        f_data_requested = FALSE;
      }
    } /* end of 'if power on' condition */
  } /* end of 'if frame time reached' condition */
}

int read_inputs(byte buff[]) {
  /* this function reads in all digital inputs and places them in the data buffer */
  /* first clear the data buffer in the area we will do bit setting */
  for (i = 0; i < 5; i++) {
    buff[i] = 0;
  }

  /* read and map in the direct digital IO pins */
  for (i = c_first_input_pin1; i <= c_last_input_pin1; i++) {
    bitWrite(buff[0], (i - c_first_input_pin1) % 8, !digitalRead(i));
  }

  for (i = c_first_input_pin2; i <= c_last_input_pin2; i++) {
    bitWrite(buff[(i - c_first_input_pin2) / 8 + 1], (i - c_first_input_pin2) % 8, !digitalRead(i));
  }

  /* now read the digital ins from each MUX bank.
      note that they already come as bytes so they can be copied straight in.
  */
  mux_Rx(0x20, 0x12, 1, &buff[5]);
  mux_Rx(0x20, 0x13, 1, &buff[6]);
  mux_Rx(0x21, 0x12, 1, &buff[7]);
  mux_Rx(0x21, 0x13, 1, &buff[8]);
  mux_Rx(0x22, 0x13, 1, &buff[9]);
  mux_Rx(0x23, 0x13, 1, &buff[10]);
  mux_Rx(0x24, 0x13, 1, &buff[11]);
  mux_Rx(0x25, 0x12, 1, &buff[12]);
  mux_Rx(0x25, 0x13, 1, &buff[13]);
  mux_Rx(0x26, 0x12, 1, &buff[14]);
  mux_Rx(0x26, 0x13, 1, &buff[15]);

  /* read the analog inputs and map to a byte */
  buff[16] = map(analogRead(A0), 0, 1023, 0, 255); /* Voltage sensor */
  buff[17] = map(analogRead(A1), 0, 1023, 0, 255); /* Temperature Sensor */
  buff[18] = map(analogRead(A2), 0, 1023, 255, 2); /* Dimmer - REVERSED - set a minimum to avoid no lights */
  buff[19] = map(analogRead(A3), 0, 1023, 0, 255); /* Rotation X */
  buff[20] = map(analogRead(A4), 0, 1023, 0, 255); /* Rotation Y */
  buff[21] = map(analogRead(A5), 0, 1023, 0, 255); /* Rotation Z */
  buff[22] = map(analogRead(A6), 0, 1023, 255, 0); /* Translation X - REVERSED */
  buff[23] = map(analogRead(A7), 0, 1023, 0, 255); /* Translation Y */
  buff[24] = map(analogRead(A8), 0, 1023, 0, 255); /* Translation Z */
  buff[25] = map(analogRead(A9), 0, 1023, 0, 255); /* Throttle */
  return 0;
}

int write_outputs(byte inputs[], byte outputs[]) {
  byte temp = 0;
  /* start by mapping in the input data, then overwrite with locally driven lights from the output buffer*/
  temp = inputs[1]; /*shortcut to map in bits 0-3 */
  bitWrite(temp, 4, bitRead(outputs[9], 7)); /* staging armed */
  bitWrite(temp, 5, (bitRead(outputs[9], 3) || bitRead(outputs[9], 4) || bitRead(outputs[9], 5) || bitRead(outputs[9], 6))); /* throttle armed */
  bitWrite(temp, 6, (bitRead(outputs[9], 4) || bitRead(outputs[9], 5) || bitRead(outputs[9], 6))); /* throttle limited */
  bitWrite(temp, 7, bitRead(outputs[9], 2)); /* SAS Power On */
  mux_Tx(0x23, 0x12, temp);  /* MUX 0x23, GPIOA */

  temp = 0; /* we are not receiving anything here */
  bitWrite(temp, 0, bitRead(outputs[7], 6)); /* Controls Fine */
  mux_Tx(0x23, 0x13, temp);  /* MUX 0x23, GPIOB */

  temp = inputs[2]; /* shortcut to map in bits 0-3 and 5. Bit 4 will be overwritten later*/

  /* output 5 is the gear indicator. It should be on if gear is down (inputs[2] bit 5 is true), off
      if down(inputs[2] bit 4 is true) and flashing otherwise
  */
  if (!(bitRead(inputs[2], 4) || bitRead(inputs[2], 5))) {
    t_gear_flash_timer += t_frame_time;
    bitWrite(temp, 5, int(t_gear_flash_timer / c_gear_light_flash) % 2);
  }
  else {
    t_gear_flash_timer = 0;
  }
  bitWrite(temp, 4, bitRead(outputs[11], 3)); /* NWS armed */
  bitWrite(temp, 6, (bitRead(outputs[11], 5) || bitRead(outputs[11], 6))); /* Brakes */
  bitWrite(temp, 7, bitRead(outputs[11], 1)); /* Lights */
  mux_Tx(0x24, 0x12, temp);  /* MUX 0x24, GPIOA */

  temp = 0; /* we are not receiving anything here */
  bitWrite(temp, 0, bitRead(outputs[11], 2)); /* Controls Fine */
  mux_Tx(0x24, 0x13, temp);  /* MUX 0x24, GPIOB */
}

int autopilot(byte databuffer[]) {
  if (bitRead(databuffer[14], 6) && !f_ap_pwr_p) {
    if (f_ap_power_state) { /* switch off */
      f_ap_power_state = false;
      f_ap_system_state = 0;
      t_ap_init_timer = 0;
      for (i = 0; i < 3; i++) {
        APSetting[i].setmode = 0;
        APSetting[i].setval = 0;
        APSetting[i].displaymode = 0;
        APSetting[i].displayval = 0;
        APSetting[i].isconn = 0;
      }
      lcd.clear();
    }
    else { /* switch on */
      f_ap_power_state = true;
      lcd.begin(40, 2);
      f_ap_system_state = 1;
    }
  }
  f_ap_pwr_p = bitRead(databuffer[14], 6);

  /* AP State Machine */
  if (f_ap_system_state == 1) { /* init state */
    if (t_ap_init_timer == 0) {
      lcd.print("Welcome to Kerbal Autopilot");
      lcd.setCursor(0, 1);
      lcd.print("Standby... Autopilot Inflating");
    }
    if (t_ap_init_timer > c_ap_init_time) {
      f_ap_system_state++;
      for (i = 0; i < 3; i++) {
        APSetting[i].setval = APModes[i][0].defval;
        APSetting[i].displayval = APModes[i][0].defval;
      }
      f_ap_screen_refresh = true;
    }
    t_ap_init_timer += t_frame_time*c_ap_subband;
  }
  if (f_ap_system_state == 2) { /* running state */
    /* map in the switch inputs */
    for (i = 0; i < 3; i++) {
      for (j = 0; j < 6; j++) {
        f_ap_inputs_p[i][j] = f_ap_inputs[i][j];
      }
    }
    f_ap_inputs[0][0] = bitRead(databuffer[13], 5);
    f_ap_inputs[0][1] = bitRead(databuffer[13], 4);
    f_ap_inputs[0][2] = bitRead(databuffer[13], 3);
    f_ap_inputs[0][3] = bitRead(databuffer[13], 2);
    f_ap_inputs[0][4] = bitRead(databuffer[13], 1);
    f_ap_inputs[0][5] = bitRead(databuffer[13], 0);
    f_ap_inputs[1][0] = bitRead(databuffer[16], 0);
    f_ap_inputs[1][1] = bitRead(databuffer[16], 1);
    f_ap_inputs[1][2] = bitRead(databuffer[16], 2);
    f_ap_inputs[1][3] = bitRead(databuffer[16], 3);
    f_ap_inputs[1][4] = bitRead(databuffer[16], 4);
    f_ap_inputs[1][5] = bitRead(databuffer[16], 5);
    f_ap_inputs[2][0] = bitRead(databuffer[15], 5);
    f_ap_inputs[2][1] = bitRead(databuffer[15], 4);
    f_ap_inputs[2][2] = bitRead(databuffer[15], 3);
    f_ap_inputs[2][3] = bitRead(databuffer[15], 2);
    f_ap_inputs[2][4] = bitRead(databuffer[15], 1);
    f_ap_inputs[2][5] = bitRead(databuffer[15], 0);

    /* Manage Switch Inputs */
    /* Master Cancel */
    if (bitRead(databuffer[14], 7) && !f_ap_cancel_p) {
      for (i = 0; i < 3; i++) {
        APSetting[i].isconn = false;
        APSetting[i].displaymode = APSetting[i].setmode;
        APSetting[i].displayval = APSetting[i].setval;
        f_ap_screen_refresh = true;
      }
    }
    f_ap_cancel_p = bitRead(databuffer[14], 7);

    /* Axis buttons */
    for (i = 0; i < 3; i++) {
      if (f_ap_inputs[i][0] && !f_ap_inputs_p[i][0]) { /* Mode Up Button */
        APSetting[i].displaymode = mod((APSetting[i].displaymode - 1), n_ap_modes[i]);
        if (APSetting[i].displaymode == APSetting[i].setmode) {
          APSetting[i].displayval = APSetting[i].setval;
        }
        else {
          APSetting[i].displayval = APModes[i][APSetting[i].displaymode].defval;
        }
        f_ap_screen_refresh = true;
      }
      if (f_ap_inputs[i][1] && !f_ap_inputs_p[i][1]) { /* Mode Dn Button */
        APSetting[i].displaymode = mod((APSetting[i].displaymode + 1), n_ap_modes[i]);
        if (APSetting[i].displaymode == APSetting[i].setmode) {
          APSetting[i].displayval = APSetting[i].setval;
        }
        else {
          APSetting[i].displayval = APModes[i][APSetting[i].displaymode].defval;
        }
        f_ap_screen_refresh = true;
      }
      if (f_ap_inputs[i][2] && !f_ap_inputs_p[i][2]) { /* Cancel Button */
        if (APSetting[i].displaymode == APSetting[i].setmode &&
            APSetting[i].displayval == APSetting[i].setval) {
          APSetting[i].isconn = false;
        }
        else {
          APSetting[i].displaymode = APSetting[i].setmode;
          APSetting[i].displayval = APSetting[i].setval;
        }
        f_ap_screen_refresh = true;
      }
      if (f_ap_inputs[i][3] && !f_ap_inputs_p[i][3]) { /* Set Button */
        APSetting[i].setmode = APSetting[i].displaymode;
        APSetting[i].setval = APSetting[i].displayval;
        APSetting[i].isconn = true;
        f_ap_screen_refresh = true;
      }
      if (f_ap_inputs[i][4]){ /* Val Up Button */
        if (!f_ap_inputs_p[i][4]) { /* First Press */
           if(APModes[i][APSetting[i].displaymode].wrap){
             APSetting[i].displayval = mod(APSetting[i].displayval + APModes[i][APSetting[i].displaymode].valstep,
                                           APModes[i][APSetting[i].displaymode].maxval);
           }
           else{
             APSetting[i].displayval = min(APSetting[i].displayval + APModes[i][APSetting[i].displaymode].valstep, 
                                           APModes[i][APSetting[i].displaymode].maxval);
           }
        }
        else{ /* Button Held */
          if (n_ap_faststep_ucount[i] < c_ap_faststep_delay){
            n_ap_faststep_ucount[i] ++;
          }
          else{
            if(APModes[i][APSetting[i].displaymode].wrap){
              APSetting[i].displayval = mod(APSetting[i].displayval + APModes[i][APSetting[i].displaymode].valstep * 
                                             APModes[i][APSetting[i].displaymode].stepmult, 
                                            APModes[i][APSetting[i].displaymode].maxval);
            }
            else{
              APSetting[i].displayval = min(APSetting[i].displayval + 
                                              APModes[i][APSetting[i].displaymode].valstep * 
                                              APModes[i][APSetting[i].displaymode].stepmult, 
                                            APModes[i][APSetting[i].displaymode].maxval);
            }
          }
        }
        f_ap_screen_refresh = true;
      }
      else{
        n_ap_faststep_ucount[i] = 0;
      }
      if (f_ap_inputs[i][5]){ /* Val Dn Button */
        if (!f_ap_inputs_p[i][5]) { /* First Press */
           if(APModes[i][APSetting[i].displaymode].wrap){
             APSetting[i].displayval = mod(APSetting[i].displayval - APModes[i][APSetting[i].displaymode].valstep, 
                                           APModes[i][APSetting[i].displaymode].maxval);
           }
           else{
             APSetting[i].displayval = max(APSetting[i].displayval - APModes[i][APSetting[i].displaymode].valstep, 
                                           APModes[i][APSetting[i].displaymode].minval);
           }

        }
        else{ /* Button Held */
          if (n_ap_faststep_dcount[i] < c_ap_faststep_delay){
            n_ap_faststep_dcount[i] ++;
          }
          else{
            if(APModes[i][APSetting[i].displaymode].wrap){
              APSetting[i].displayval = mod(APSetting[i].displayval - APModes[i][APSetting[i].displaymode].valstep * 
                                             APModes[i][APSetting[i].displaymode].stepmult,
                                            APModes[i][APSetting[i].displaymode].maxval);
            }
            else{
              APSetting[i].displayval = max(APSetting[i].displayval - 
                                              APModes[i][APSetting[i].displaymode].valstep *
                                              APModes[i][APSetting[i].displaymode].stepmult, 
                                            APModes[i][APSetting[i].displaymode].minval);
            }
          }
        }
        f_ap_screen_refresh = true;
      }
      else{
        n_ap_faststep_dcount[i] = 0;
      }
    } /* end for loop */
  } /* end if AP state = 2 */

  /* if requested, redraw the screen */
  if (f_ap_screen_refresh) {
    /* Build line 1 */
    for (i = 0; i < 3; i++) {
      if (APSetting[i].displaymode != APSetting[i].setmode) {
        sprintf(s_ap_text_cons[i], "<%s>", APModes[i][APSetting[i].displaymode].mode);
      }
      else {
        sprintf(s_ap_text_cons[i], "%s", APModes[i][APSetting[i].displaymode].mode);
      }
      pad(s_ap_text_cons[i]);
    }
    sprintf(s_ap_text1, " %s|%s|%s ", s_ap_text_cons[0], s_ap_text_cons[1], s_ap_text_cons[2]);

    /* Build line 2 */
    for (i = 0; i < 3; i++) {
      if (APSetting[i].displayval != APSetting[i].setval || APSetting[i].displaymode != APSetting[i].setmode) {
        sprintf(s_ap_text_cons[i], "<%s%d%s>", APModes[i][APSetting[i].displaymode].prefix, 
                                               APSetting[i].displayval, 
                                               APModes[i][APSetting[i].displaymode].suffix);
      }
      else {
        if (APSetting[i].isconn) {
          sprintf(s_ap_text_cons[i], "%s%d%s", APModes[i][APSetting[i].displaymode].prefix, 
                                               APSetting[i].displayval, 
                                               APModes[i][APSetting[i].displaymode].suffix);
        }
        else {
          sprintf(s_ap_text_cons[i], "!!%s%d%s!!", APModes[i][APSetting[i].displaymode].prefix, 
                                                   APSetting[i].displayval, 
                                                   APModes[i][APSetting[i].displaymode].suffix);
        }
      }
      pad(s_ap_text_cons[i]);
    }

    sprintf(s_ap_text2, " %s|%s|%s ", s_ap_text_cons[0], s_ap_text_cons[1], s_ap_text_cons[2]);

    lcd.clear();
    lcd.print(s_ap_text1);
    lcd.setCursor(0, 1);
    lcd.print(s_ap_text2);
    f_ap_screen_refresh = false;
  }

  /* Write data to the buffer for transmit */
  /* Status byte - power, state and connections */
  databuffer[29] = 0;
  bitWrite(databuffer[29], 0, f_ap_power_state);
  bitWrite(databuffer[29], 1, f_ap_system_state == 2);
  bitWrite(databuffer[29], 2, APSetting[0].isconn);
  bitWrite(databuffer[29], 3, APSetting[1].isconn);
  bitWrite(databuffer[29], 4, APSetting[2].isconn); 
  databuffer[30] = APSetting[0].setmode;
  databuffer[31] = APSetting[1].setmode;
  databuffer[32] = APSetting[2].setmode;  
  databuffer[33] = highByte(APSetting[0].setval);
  databuffer[34] = lowByte(APSetting[0].setval);  
  databuffer[35] = highByte(APSetting[1].setval);
  databuffer[36] = lowByte(APSetting[1].setval);
  databuffer[37] = highByte(APSetting[2].setval);
  databuffer[38] = lowByte(APSetting[2].setval); 
}

