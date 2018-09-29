/* Definitions */
#define TRUE 1
#define FALSE 0
// #define DEBUG                /* This flag will enable debug code forcing write direct to serial out ignoring panel connection */

/* Variables */
byte x_databuffer[19];                  /* byte buffer for managing outputs */
byte x_inputbuffer[1];                  /* byte buffer for managing inputs */
int f_data_received = 0;                /* data received flag */
int f_data_requested = 0;               /* data requested flag */
int i;                                  /* general loop counter */
int j;                                  /* general loop counter */
int n_mux_chips_detected = 0;           /* number of MUX chips detected in the IBIT */
int f_critical_error = 0;               /* critical error detected flag */
int f_error_light_state = 0;            /* error light flash state */
int f_serial_state = 0;                 /* state of serial comm */

unsigned long t_overun_light = 0;       /* timer for overun light hold calculation */
unsigned long t_current_frame = 0;      /* current frame start time */
unsigned long t_frame_time = 0;         /* the simulation time for the current frame */
unsigned long t_last_frame = 0;         /* time since last frame */
unsigned long t_frame_actual = 0;       /* actual time it took to process the current frame */
unsigned long t_run_time = 0;           /* time since main power on */
unsigned long t_power_on = 0;           /* time when main power came on */
unsigned long t_gear_flash_timer = 0;   /* timer for gear light flash calculation */
unsigned long t_last_serial_time = 0;   /* time since last serial data arrived */
unsigned long t_error_light = 0;        /* timer for error light flashing */


/* constants */
const int c_power_light_flash = 1000;   /* power light flash rate [ms] */
const int c_num_mux_chips = 5;          /* the number of MCP23017 chips installed [-]*/
const int c_error_code_mux_missing = 1; /* error code if MUX count is incorrect [-]*/
const int c_frame_time_target = 10;     /* target frame time [ms]*/
const int c_temp_max = 160;             /* overtemp limit, stop. [-]*/
const int c_overtemp_error_code = 2;    /* error code if overtemp limit exceeded [-]*/
const int c_gear_light_flash = 200;     /* gear light flash rate [ms]*/
const int c_first_mux_address = 32;     /* the first I2C address in the MUX range [-]*/
const int c_last_mux_address = 40;      /* the last I2C address in the MUX range [-]*/
const int c_light_bit_time = 100;       /* time to delay to allow light BIT test to be seen [ms]*/
const int c_light_bit_time_d = 500;     /* time to delay to allow light BIT test to be seen - slower for debug [ms]*/
const int c_serial_timeout = 1000;      /* serial timeout [ms]*/
const int c_error_light_flash = 250;    /* no data flash rate for error light [ms]*/
const int c_light_brigtness = 5;        /* PWM value for light brightness */
const int c_error_flash_intensity = 10; /* PWM value for error light flashing (no connection) */
const long c_serial_speed = 115200;     /* serial bus baud rate [baud]*/

/* pin mappings */
const int c_overrun_led_pin = 8;
const int c_power_led_R_pin = 9;
const int c_power_led_G_pin = 10;
const int c_sys_light_enable_1 = 11;
const int c_sys_light_enable_2 = 12;
const int c_error_led_pin = 13;

/* pin ranges */
const int c_first_input_pin1 = 2;       /* the first pin used for digital IO */
const int c_last_input_pin1 = 5;        /* the last input pin used for digital IO */
const int c_first_input_pin2 = 14;      /* the first pin used for digital IO */
const int c_last_input_pin2 = 16;       /* the last input pin used for digital IO */
const int c_first_pwm_pin = 8;          /* the first pin used for digital output */
const int c_last_pwm_pin = 13;          /* the last output pin used for digital IO */



/* structs */

/* function prototypes*/
int read_inputs(byte buff[]);
int write_outputs(byte inputs[], byte outputs[]);


