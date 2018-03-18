void sys_error(void);
void light_flash(int pin, unsigned long *timer, int flashtime);
void light_flash_pwm(int pin, unsigned long *timer, int *state, int flashtime, int intensity);
void light_dim_ctl(int pin, int cond, int on_val, int off_val);
void mux_Tx(int adr, int reg, byte data);
void mux_Rx(int adr, int reg, int numbytes, byte *data);
void pad(char* text);
int mod(int x, int m);


void sys_error(int code) {
  /* this function is called if a critical error exists. It flashes the error light as per the error code
     and blocks all other functions
  */
  while (true) {
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

void light_dim_ctl(int pin, int cond, int on_val, int off_val) {
  if (cond) {
    analogWrite(pin, on_val);
  }
  else {
    analogWrite(pin, off_val);
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

void pad(char* text) {
  char format[10];
  int offset;
  char temp[13];

  offset = (12 - strlen(text)) / 2 + strlen(text);
  sprintf(format, "%%+%ds", offset);
  sprintf(temp, format, text);
  sprintf(text, "%-12s", temp);
}

int mod(int x, int m) {
  int r = x % m;
  return r < 0 ? r + m : r;
}

