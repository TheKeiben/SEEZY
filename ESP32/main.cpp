#include <Arduino.h>
#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <rmw_microros/rmw_microros.h>
#include <geometry_msgs/msg/twist.h>
#include <geometry_msgs/msg/vector3.h> 
#include <std_msgs/msg/int32.h>
#include "driver/gpio.h" 
#include <std_srvs/srv/trigger.h>

// --- FUNCTION PROTOTYPES ---
void IRAM_ATTR left_encoder_isr();
void IRAM_ATTR right_encoder_isr();
void setMotors(int leftSpeed, int rightSpeed);
void stopAndResetDriver();
void twist_callback(const void * msgin);
void timer_callback(rcl_timer_t * timer, int64_t last_call_time);
void reset_callback(const void * req, void * res);
bool create_entities();
void destroy_entities();

// --- HARDWARE DEFINITIONS ---
const int LPWM = 23; const int LDIR = 33; 
const int RPWM = 22; const int RDIR = 21; 
const int MEN  = 32; 
const int LPWM_CHANNEL = 0; const int RPWM_CHANNEL = 1;
const int LEA = 19; const int LEB = 16; 
const int REA = 18; const int REB = 17; 

const int freq = 20000;      
const int resolution = 8;    

volatile long left_ticks = 0;  
volatile long right_ticks = 0; 
long prev_left_ticks = 0;      
long prev_right_ticks = 0;     

unsigned long last_pid_time = 0; 
unsigned long lastCmdTime = 0;   
bool isStopped = true;           

// --- PID PARAMETERS ---
float Kp = 0.003; 
float Ki = 0.0005; 
float Kd = 0.0;   

float target_left_speed = 0.0; float target_right_speed = 0.0;
float actual_left_speed = 0.0; float actual_right_speed = 0.0;
float integral_left = 0.0;     float integral_right = 0.0;
float prev_error_left = 0.0;   float prev_error_right = 0.0;
int current_pwm_left = 0;      int current_pwm_right = 0;     

// --- ROS 2 VARIABLES ---
rcl_publisher_t left_pub;        
rcl_publisher_t right_pub;       
rcl_publisher_t debug_left_pub;  
rcl_publisher_t debug_right_pub; 
rcl_subscription_t twist_sub;    
rcl_service_t reset_service;

geometry_msgs__msg__Twist twist_msg;         
geometry_msgs__msg__Vector3 debug_left_msg;  
geometry_msgs__msg__Vector3 debug_right_msg; 
std_msgs__msg__Int32 left_msg;               
std_msgs__msg__Int32 right_msg;              
std_srvs__srv__Trigger_Request reset_req;
std_srvs__srv__Trigger_Response reset_res;

rclc_executor_t executor;   
rclc_support_t support;     
rcl_allocator_t allocator;  
rcl_node_t node;            
rcl_timer_t timer;          

// --- STATE MACHINE ENUM ---
enum states {
  WAITING_AGENT,
  AGENT_AVAILABLE,
  AGENT_CONNECTED,
  AGENT_DISCONNECTED
} state;

// Safe check macro: If an entity fails to initialize, safely abort so the state machine can retry
#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){ return false; }}
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){}}

// --- FAST INTERRUPTS ---
void IRAM_ATTR left_encoder_isr() {
  if (gpio_get_level((gpio_num_t)LEA) == gpio_get_level((gpio_num_t)LEB)) left_ticks--;
  else left_ticks++;
}

void IRAM_ATTR right_encoder_isr() {
  if (gpio_get_level((gpio_num_t)REA) == gpio_get_level((gpio_num_t)REB)) right_ticks++;
  else right_ticks--;
}

// --- MOTOR CONTROL ---
void setMotors(int leftSpeed, int rightSpeed) {
  digitalWrite(LDIR, leftSpeed >= 0 ? LOW : HIGH);               
  ledcWrite(LPWM_CHANNEL, abs(leftSpeed));     

  digitalWrite(RDIR, rightSpeed >= 0 ? HIGH : LOW);
  ledcWrite(RPWM_CHANNEL, abs(rightSpeed));      
}

void stopAndResetDriver() {
  setMotors(0, 0);                 
  digitalWrite(MEN, HIGH);         
  isStopped = true;                
  
  integral_left = 0; integral_right = 0;
  prev_error_left = 0; prev_error_right = 0;
  current_pwm_left = 0; current_pwm_right = 0;
}

// --- ROS 2 CALLBACKS ---
void twist_callback(const void * msgin) {
  const geometry_msgs__msg__Twist * msg = (const geometry_msgs__msg__Twist *)msgin;
  float x = msg->linear.x; 
  float z = msg->angular.z;

  if (abs(x) < 0.01 && abs(z) < 0.01) {
    target_left_speed = 0.0; target_right_speed = 0.0;
    if (!isStopped) stopAndResetDriver();
  } else {
    const float WHEEL_RADIUS = 0.0975;     
    const float WHEEL_SEPARATION = 0.38;   
    const float TICKS_PER_REV = 76600.0;   
    
    float wheel_circumference = 2.0 * PI * WHEEL_RADIUS; 
    float linear_scale_ticks = TICKS_PER_REV / wheel_circumference; 
    float angular_scale_ticks = linear_scale_ticks * (WHEEL_SEPARATION / 2.0); 
    
    target_left_speed = (x * linear_scale_ticks) - (z * angular_scale_ticks);
    target_right_speed = (x * linear_scale_ticks) + (z * angular_scale_ticks);
    
    digitalWrite(MEN, LOW); 
    isStopped = false;              
  }
  lastCmdTime = millis(); 
}

void timer_callback(rcl_timer_t * timer, int64_t last_call_time) {
  RCLC_UNUSED(last_call_time); 
  if (timer != NULL) { 
    left_msg.data = left_ticks; right_msg.data = right_ticks;
    RCSOFTCHECK(rcl_publish(&left_pub, &left_msg, NULL));
    RCSOFTCHECK(rcl_publish(&right_pub, &right_msg, NULL));

    debug_left_msg.x = target_left_speed; debug_left_msg.y = actual_left_speed; debug_left_msg.z = (float)current_pwm_left;
    RCSOFTCHECK(rcl_publish(&debug_left_pub, &debug_left_msg, NULL));

    debug_right_msg.x = target_right_speed; debug_right_msg.y = actual_right_speed; debug_right_msg.z = (float)current_pwm_right;
    RCSOFTCHECK(rcl_publish(&debug_right_pub, &debug_right_msg, NULL));
  }
}

void reset_callback(const void * req, void * res) {
    std_srvs__srv__Trigger_Response * res_in = (std_srvs__srv__Trigger_Response *) res;
    res_in->success = true;
    ESP.restart(); 
}

// --- STATE MACHINE ENTITY MANAGEMENT ---
bool create_entities() {
  allocator = rcl_get_default_allocator();
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
  RCCHECK(rclc_node_init_default(&node, "esp32_base_node", "", &support));
  
  RCCHECK(rclc_publisher_init_default(&left_pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "/encoder/left"));
  RCCHECK(rclc_publisher_init_default(&right_pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "/encoder/right"));
  RCCHECK(rclc_publisher_init_default(&debug_left_pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Vector3), "/debug/left"));
  RCCHECK(rclc_publisher_init_default(&debug_right_pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Vector3), "/debug/right"));
  
  RCCHECK(rclc_subscription_init_default(&twist_sub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), "/cmd_vel"));
  RCCHECK(rclc_service_init_default(&reset_service, &node, ROSIDL_GET_SRV_TYPE_SUPPORT(std_srvs, srv, Trigger), "/seezy/reset_esp"));
  RCCHECK(rclc_timer_init_default2(&timer, &support, RCL_MS_TO_NS(50), timer_callback, true));
  
  RCCHECK(rclc_executor_init(&executor, &support.context, 3, &allocator));
  RCCHECK(rclc_executor_add_subscription(&executor, &twist_sub, &twist_msg, &twist_callback, ON_NEW_DATA));
  RCCHECK(rclc_executor_add_timer(&executor, &timer));
  RCCHECK(rclc_executor_add_service(&executor, &reset_service, &reset_req, &reset_res, reset_callback));
  
  return true;
}

void destroy_entities() {
  rmw_context_t * rmw_context = rcl_context_get_rmw_context(&support.context);
  (void) rmw_uros_set_context_entity_destroy_session_timeout(rmw_context, 0);

  rcl_publisher_fini(&left_pub, &node);
  rcl_publisher_fini(&right_pub, &node);
  rcl_publisher_fini(&debug_left_pub, &node);
  rcl_publisher_fini(&debug_right_pub, &node);
  rcl_subscription_fini(&twist_sub, &node);
  rcl_service_fini(&reset_service, &node);
  rcl_timer_fini(&timer);
  rclc_executor_fini(&executor);
  rcl_node_fini(&node);
  rclc_support_fini(&support);
}

// --- SETUP ---
void setup() {
  set_microros_transports(); 
  
  pinMode(LDIR, OUTPUT); pinMode(RDIR, OUTPUT); pinMode(MEN, OUTPUT);
  pinMode(LEA, INPUT); pinMode(LEB, INPUT); pinMode(REA, INPUT); pinMode(REB, INPUT);
  attachInterrupt(digitalPinToInterrupt(LEA), left_encoder_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(REA), right_encoder_isr, CHANGE);

  ledcSetup(LPWM_CHANNEL, freq, resolution); ledcAttachPin(LPWM, LPWM_CHANNEL);
  ledcSetup(RPWM_CHANNEL, freq, resolution); ledcAttachPin(RPWM, RPWM_CHANNEL);

  stopAndResetDriver(); 
  state = WAITING_AGENT;
}

// --- MAIN LOOP ---
void loop() {
  // State Machine Switch
  switch (state) {
    case WAITING_AGENT:
      // Ping the Jetson every 100ms. If it replies, transition state.
      if (RMW_RET_OK == rmw_uros_ping_agent(100, 1)) {
        state = AGENT_AVAILABLE;
      }
      break;

    case AGENT_AVAILABLE:
      if (create_entities()) {
        state = AGENT_CONNECTED;
      } else {
        destroy_entities();
        state = WAITING_AGENT;
      }
      break;

    case AGENT_CONNECTED:
      // Continuously check if the agent is still alive
      if (RMW_RET_OK != rmw_uros_ping_agent(100, 1)) {
        state = AGENT_DISCONNECTED;
      } else {
        // Spin ROS 2 executor
        rclc_executor_spin_some(&executor, RCL_MS_TO_NS(5));
      }
      break;

    case AGENT_DISCONNECTED:
      stopAndResetDriver();
      destroy_entities();
      state = WAITING_AGENT;
      break;
  }

  // --- MOTOR PID LOOP (Only runs if agent is connected and publishing) ---
  if (state == AGENT_CONNECTED) {
    unsigned long now = millis();

    if (!isStopped && (now - lastCmdTime > 1000)) {
      stopAndResetDriver();
    }

    if (now - last_pid_time >= 20) {
      float dt = (now - last_pid_time) / 1000.0; 
      last_pid_time = now; 

      long curr_left = left_ticks;
      long curr_right = right_ticks;

      actual_left_speed = (curr_left - prev_left_ticks) / dt;
      actual_right_speed = (curr_right - prev_right_ticks) / dt;
      
      prev_left_ticks = curr_left;
      prev_right_ticks = curr_right;

      if (!isStopped) {
        float error_left = target_left_speed - actual_left_speed;
        integral_left += error_left * dt;
        integral_left = constrain(integral_left, -50000, 50000); 
        float derivative_left = (error_left - prev_error_left) / dt;
        float output_left = (Kp * error_left) + (Ki * integral_left) + (Kd * derivative_left);
        prev_error_left = error_left;

        float error_right = target_right_speed - actual_right_speed;
        integral_right += error_right * dt;
        integral_right = constrain(integral_right, -50000, 50000); 
        float derivative_right = (error_right - prev_error_right) / dt;
        float output_right = (Kp * error_right) + (Ki * integral_right) + (Kd * derivative_right);
        prev_error_right = error_right;

        current_pwm_left = constrain((int)output_left, -255, 255);
        current_pwm_right = constrain((int)output_right, -255, 255);

        setMotors(current_pwm_left, current_pwm_right);
      }
    }
  }
}