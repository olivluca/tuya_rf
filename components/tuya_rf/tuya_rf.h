#pragma once

#include "esphome/components/remote_base/remote_base.h"
#include "esphome/core/component.h"
#include "globals.h"
#include <vector>

namespace esphome {
namespace tuya_rf {

#if defined(USE_LIBRETINY)
struct RemoteReceiverComponentStore {
  static void gpio_intr(RemoteReceiverComponentStore *arg);

  /// Stores the time (in micros) that the leading/falling edge happened at
  ///  * An even index means a falling edge appeared at the time stored at the index
  ///  * An uneven index means a rising edge appeared at the time stored at the index
  volatile uint32_t *buffer{nullptr};
  /// The position last written to
  volatile uint32_t buffer_write_at;
  /// The position last read from
  uint32_t buffer_read_at{0};
  bool overflow{false};
  uint32_t buffer_size{1000};
  uint32_t filter_us{10};
  ISRInternalGPIOPin pin;
};
#endif

class TuyaRfComponent : public remote_base::RemoteTransmitterBase,
                        public remote_base::RemoteReceiverBase, 
                                   public Component
{
 public:
  explicit TuyaRfComponent(InternalGPIOPin *sclk_pin, InternalGPIOPin *mosi_pin, InternalGPIOPin *csb_pin, InternalGPIOPin *fcsb_pin,
     InternalGPIOPin *tx_pin, InternalGPIOPin *rx_pin) : remote_base::RemoteTransmitterBase(tx_pin), remote_base::RemoteReceiverBase(rx_pin) {
      this->sclk_pin_=sclk_pin;
      this->mosi_pin_=mosi_pin;
      this->csb_pin_=csb_pin;
      this->fcsb_pin_=fcsb_pin;
      tuya_sclk = this->sclk_pin_->get_pin();
      tuya_mosi = this->mosi_pin_->get_pin();
      tuya_csb = this->csb_pin_->get_pin();
      tuya_fcsb = this->fcsb_pin_->get_pin();
  }
  void setup() override;

  void dump_config() override;
  void loop() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  void set_receiver_disabled(bool receiver_disabled) { this->receiver_disabled_ = receiver_disabled; }
  void set_buffer_size(uint32_t buffer_size) { this->buffer_size_ = buffer_size; }
  void set_filter_us(uint32_t filter_us) { this->filter_us_ = filter_us; }
  void set_start_pulse_min_us(uint32_t start_pulse_min_us) { this->start_pulse_min_us_ = start_pulse_min_us; }
  void set_start_pulse_max_us(uint32_t start_pulse_max_us) { this->start_pulse_max_us_ = start_pulse_max_us; }
  void set_end_pulse_us(uint32_t end_pulse_us) { this->end_pulse_us_ = end_pulse_us; }
  void set_initial_frequency(uint32_t frequency) { this->frequency_ = frequency; }
  void turn_on_receiver();
  void turn_off_receiver();
  bool set_frequency(uint32_t frequency);

 protected:
  void send_internal(uint32_t send_times, uint32_t send_wait) override;

  void mark_(uint32_t usec);

  void space_(uint32_t usec);

  void await_target_time_();
  void set_receiver(bool on);
  uint32_t target_time_;
#if defined(USE_LIBRETINY)
  RemoteReceiverComponentStore store_;
  HighFrequencyLoopRequester high_freq_;
#endif

  InternalGPIOPin *sclk_pin_;
  InternalGPIOPin *mosi_pin_;
  InternalGPIOPin *csb_pin_;
  InternalGPIOPin *fcsb_pin_;
  
  bool receiver_disabled_{false};
  uint32_t buffer_size_{};
  uint32_t filter_us_{50};
  uint32_t start_pulse_min_us_{6000};
  uint32_t start_pulse_max_us_{10000};
  uint32_t end_pulse_us_{50000};
  uint32_t frequency_{433920000};

  bool transmitting_{false};
  bool receive_started_{false};
  uint32_t old_write_at_{0};
};

}  // namespace tuya_rf
}  // namespace esphome
