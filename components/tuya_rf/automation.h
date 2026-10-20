#pragma once

#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "tuya_rf.h"

namespace esphome {
namespace tuya_rf {

template<typename... Ts> class TurnOffReceiverAction : public Action<Ts...> {
 public:
  TurnOffReceiverAction(TuyaRfComponent *tuya_rf) : tuya_rf_(tuya_rf) {}

  void play(const Ts &...x) override { this->tuya_rf_->turn_off_receiver(); this->play_next_(x...);}

 protected:
  TuyaRfComponent *tuya_rf_;
};

template<typename... Ts> class TurnOnReceiverAction : public Action<Ts...> {
 public:
  TurnOnReceiverAction(TuyaRfComponent *tuya_rf) : tuya_rf_(tuya_rf) {}

  void play(const Ts &...x) override { this->tuya_rf_->turn_on_receiver(); this->play_next_(x...);}

 protected:
  TuyaRfComponent *tuya_rf_;
};

template<typename... Ts> class SetFrequencyAction : public Action<Ts...> {
 public:
  SetFrequencyAction(TuyaRfComponent *tuya_rf) : tuya_rf_(tuya_rf) {}
  TEMPLATABLE_VALUE(uint32_t, frequency)

  void play(const Ts &...x) override { this->tuya_rf_->set_frequency(this->frequency_.value(x...)); this->play_next_(x...);}

 protected:
  TuyaRfComponent *tuya_rf_;
};

}  // namespace tuya_rf
}  // namespace esphome
