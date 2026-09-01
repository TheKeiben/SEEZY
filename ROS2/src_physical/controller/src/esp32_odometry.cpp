#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2/LinearMath/Quaternion.h>
#include <cmath>

class Esp32Odometry : public rclcpp::Node
{
public:
    Esp32Odometry() : Node("esp32_odometry"), x_(0.0), y_(0.0), th_(0.0), first_read_(true)
    {   
        // 1. Declare parameters for robot physical properties
        this->declare_parameter("wheel_radius", 0.0975);
        this->declare_parameter("wheel_separation", 0.33);
        this->declare_parameter("ticks_per_rev", 38300.0);

        wheel_radius_ = this->get_parameter("wheel_radius").as_double();
        wheel_separation_ = this->get_parameter("wheel_separation").as_double();
        ticks_per_rev_ = this->get_parameter("ticks_per_rev").as_double();

        // 2. Set QoS profile to Best Effort (ideal for unreliable network/microcontrollers)
        rclcpp::QoS qos_profile(10);
        qos_profile.best_effort();

        // 3. Subscriptions to encoder topics
        left_sub_ = this->create_subscription<std_msgs::msg::Int32>(
        "/encoder/left", qos_profile, std::bind(&Esp32Odometry::leftCallback, this, std::placeholders::_1));

        right_sub_ = this->create_subscription<std_msgs::msg::Int32>(
        "/encoder/right", qos_profile, std::bind(&Esp32Odometry::rightCallback, this, std::placeholders::_1));

        // 4. Publishers and TF Broadcaster
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("/odom", 10);
        tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

        // 5. Timer for calculation loop (20Hz)
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(50), std::bind(&Esp32Odometry::timerCallback, this));
    }

private:
    void leftCallback(const std_msgs::msg::Int32::SharedPtr msg) { left_ticks_ = msg->data; }
    void rightCallback(const std_msgs::msg::Int32::SharedPtr msg) { right_ticks_ = msg->data; }

    void timerCallback()
    {
        // Initialization on first run
        if (first_read_) {
            prev_left_ticks_ = left_ticks_;
            prev_right_ticks_ = right_ticks_;
            first_read_ = false;
            last_time_ = this->get_clock()->now();
            return;
        }

        // Calculate ticks difference
        long d_left_ticks = left_ticks_ - prev_left_ticks_;
        long d_right_ticks = right_ticks_ - prev_right_ticks_;

        prev_left_ticks_ = left_ticks_;
        prev_right_ticks_ = right_ticks_;

        // Convert ticks to meters
        double dist_per_tick = (2.0 * M_PI * wheel_radius_) / ticks_per_rev_;
        double d_left = d_left_ticks * dist_per_tick;
        double d_right = d_right_ticks * dist_per_tick;

        // Calculate robot displacement and rotation
        double d_center = (d_left + d_right) / 2.0;
        double d_th = (d_right - d_left) / wheel_separation_;

        // Update global position using Runge-Kutta approximation
        x_ += d_center * cos(th_ + d_th / 2.0);
        y_ += d_center * sin(th_ + d_th / 2.0);
        th_ += d_th;

        // Calculate velocities
        auto now = this->get_clock()->now();
        double dt = (now - last_time_).seconds();
        last_time_ = now;
        double vx = (dt > 0) ? d_center / dt : 0.0;
        double vth = (dt > 0) ? d_th / dt : 0.0;

        publishOdomAndTF(now, vx, vth);
    }

    void publishOdomAndTF(rclcpp::Time now, double vx, double vth)
    {
        // Broadcast Transform (TF): odom -> base_footprint
        geometry_msgs::msg::TransformStamped t;
        t.header.stamp = now;
        t.header.frame_id = "odom";
        t.child_frame_id = "base_footprint";
        t.transform.translation.x = x_;
        t.transform.translation.y = y_;
        t.transform.translation.z = 0.0;

        tf2::Quaternion q;
        q.setRPY(0, 0, th_);
        t.transform.rotation.x = q.x();
        t.transform.rotation.y = q.y();
        t.transform.rotation.z = q.z();
        t.transform.rotation.w = q.w();

        tf_broadcaster_->sendTransform(t);

        // Publish Odometry message
        nav_msgs::msg::Odometry odom;
        odom.header.stamp = now;
        odom.header.frame_id = "odom";
        odom.child_frame_id = "base_footprint";
        odom.pose.pose.position.x = x_;
        odom.pose.pose.position.y = y_;
        odom.pose.pose.orientation = t.transform.rotation;
        odom.twist.twist.linear.x = vx;
        odom.twist.twist.angular.z = vth;

        odom_pub_->publish(odom);
    }

    // Class members
    double wheel_radius_, wheel_separation_, ticks_per_rev_;
    long left_ticks_ = 0, right_ticks_ = 0;
    long prev_left_ticks_ = 0, prev_right_ticks_ = 0;
    double x_, y_, th_;
    bool first_read_;
    rclcpp::Time last_time_;
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr left_sub_;
    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr right_sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<Esp32Odometry>());
    rclcpp::shutdown();
    return 0;
}