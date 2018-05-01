void sys_error(void);
void light_flash(int pin, unsigned long *timer, int flashtime);
void light_flash_pwm(int pin, unsigned long *timer, int *state, int flashtime, int intensity);
void light_dim_ctl(int pin, int cond, int on_val, int off_val);
void mux_Tx(int adr, int reg, byte data);
void mux_Rx(int adr, int reg, int numbytes, byte *data);
int mod(int x, int m);
void printBits(byte myByte);


void sys_error(int code) {
  /* this function is called if a critical error exists. It flashes the error light as per the error code
     and blocks all other functions
  */
  while (true) {
    digitalWrite(c_power_led_R_pin, HIGH);
    digitalWrite(c_power_led_G_pin, LOW);
    for (int i = 0; i < code; i++) {
      digitalWrite(c_error_led_pin, HIGH);
      delay(200);
      digitalWrite(c_error_led_pin, LOW);
      delay(200);
    }
    delay(1000);
  }
}

void light_flash(int pin, unsigned long *timer, int flashtime) {
  /* this function will flash an output at the given time interval */
  *timer += t_frame_time;
  if (*timer > flashtime) { /* check for the timer to expire */
    *timer = 0; /* it has expired, reset the timer */
    digitalRead(pin) ? digitalWrite(pin, LOW) : digitalWrite(pin, HIGH); /* set the pin to the opposite of whater it is now */
  }
}

void light_flash_pwm(int pin, unsigned long *timer, int *state, int flashtime, int intensity) {
  /* this function will flash an output at the given time interval */
  *timer += t_frame_time;
  if (*timer > flashtime) { /* check for the timer to expire */
    *timer = 0; /* it has expired, reset the timer */
    if (*state) {
      analogWrite(pin, intensity);
      *state = 0;
    }
    else {
      analogWrite(pin, 0);
      *state = 1;
    }
  }
}


void mux_Tx(int adr, int reg, byte data) {
  /* This function will send data to a MCP23017 chip */
  Wire.beginTransmission(adr);     /* address the chip */
  Wire.write(reg);                 /* point to the register of choice */
  Wire.write(data);                /* send the data */
  Wire.endTransmission();          /* end the transmission */
}

void mux_Rx(int adr, int reg, int numbytes, byte *data) {
  /* This function will request n bytes of data from a MCP23017 chip */
  Wire.beginTransmission(adr);     /* address the chip */
  Wire.write(reg);                 /* point to the register of choice */
  Wire.endTransmission();          /* end the transmission */
  Wire.requestFrom(adr, numbytes); /* request the data */
  *data = Wire.read();
}

int mod(int x, int m) {
  int r = x % m;
  return r < 0 ? r + m : r;
}

void printBits(byte myByte){
 for(byte mask = 0x80; mask; mask >>= 1){
   if(mask  & myByte)
       Serial.print('1');
   else
       Serial.print('0');
 }
}

