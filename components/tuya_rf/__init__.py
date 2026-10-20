import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome import pins
from esphome.components import remote_base
from esphome.const import (
    CONF_BUFFER_SIZE,
    CONF_DUMP,
    CONF_FILTER,
    CONF_FREQUENCY,
    CONF_ID,
    CONF_IDLE,
    CONF_TOLERANCE,
    CONF_TYPE,
    CONF_MEMORY_BLOCKS,
    CONF_RMT_CHANNEL,
    CONF_VALUE,
)
CONF_RECEIVER_DISABLED = "receiver_disabled"
CONF_RX_PIN = "rx_pin"
CONF_TX_PIN = "tx_pin"
CONF_START_PULSE_MIN = "start_pulse_min"
CONF_START_PULSE_MAX = "start_pulse_max"
CONF_END_PULSE = "end_pulse"
CONF_SCLK_PIN = "sclk_pin"
CONF_MOSI_PIN = "mosi_pin"
CONF_CSB_PIN = "csb_pin"
CONF_FCSB_PIN = "fcsb_pin"
CONF_RECEIVER_ID = "receiver_id"

from esphome.core import CORE, TimePeriod

AUTO_LOAD = ["remote_base"]
DEPENDENCIES = ["libretiny"]

tuya_rf_ns = cg.esphome_ns.namespace("tuya_rf")
remote_base_ns = cg.esphome_ns.namespace("remote_base")

ToleranceMode = remote_base_ns.enum("ToleranceMode")

TYPE_PERCENTAGE = "percentage"
TYPE_TIME = "time"

TOLERANCE_MODE = {
    TYPE_PERCENTAGE: ToleranceMode.TOLERANCE_MODE_PERCENTAGE,
    TYPE_TIME: ToleranceMode.TOLERANCE_MODE_TIME,
}

TOLERANCE_SCHEMA = cv.typed_schema(
    {
        TYPE_PERCENTAGE: cv.Schema(
            {cv.Required(CONF_VALUE): cv.All(cv.percentage_int, cv.uint32_t)}
        ),
        TYPE_TIME: cv.Schema(
            {
                cv.Required(CONF_VALUE): cv.All(
                    cv.positive_time_period_microseconds,
                    cv.Range(max=TimePeriod(microseconds=4294967295)),
                )
            }
        ),
    },
    lower=True,
    enum=TOLERANCE_MODE,
)

TuyaRfComponent = tuya_rf_ns.class_(
    "TuyaRfComponent", remote_base.RemoteReceiverBase, remote_base.RemoteTransmitterBase, cg.Component
)

TurnOffReceiverAction = tuya_rf_ns.class_("TurnOffReceiverAction", automation.Action)
TurnOnReceiverAction = tuya_rf_ns.class_("TurnOnReceiverAction", automation.Action)
SetFrequencyAction = tuya_rf_ns.class_("SetFrequencyAction", automation.Action)

TUYA_RF_ACTION_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_RECEIVER_ID): cv.use_id(TuyaRfComponent),
    }
)

@automation.register_action("tuya_rf.turn_on_receiver", TurnOnReceiverAction, TUYA_RF_ACTION_SCHEMA, synchronous=True)
async def tuya_rf_turn_on_receiver_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_RECEIVER_ID])
    return cg.new_Pvariable(action_id, template_arg, paren)

@automation.register_action("tuya_rf.turn_off_receiver", TurnOffReceiverAction, TUYA_RF_ACTION_SCHEMA, synchronous=True)
async def tuya_rf_turn_off_receiver_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_RECEIVER_ID])
    return cg.new_Pvariable(action_id, template_arg, paren)


# Frequency bands supported by the CMT2300A (AN199 table 3)
FREQUENCY_BANDS = [
    (126.33e6, 170e6),
    (189.5e6, 340e6),
    (379e6, 510e6),
    (758e6, 1020e6),
]


def validate_frequency(value):
    value = cv.frequency(value)
    if not any(low <= value <= high for low, high in FREQUENCY_BANDS):
        bands = ", ".join(f"{low/1e6:g}-{high/1e6:g}MHz" for low, high in FREQUENCY_BANDS)
        raise cv.Invalid(f"Frequency must be in one of these bands: {bands}")
    return value


@automation.register_action(
    "tuya_rf.set_frequency",
    SetFrequencyAction,
    TUYA_RF_ACTION_SCHEMA.extend(
        {cv.Required(CONF_FREQUENCY): cv.templatable(validate_frequency)}
    ),
    synchronous=True,
)
async def tuya_rf_set_frequency_to_code(config, action_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_RECEIVER_ID])
    var = cg.new_Pvariable(action_id, template_arg, paren)
    frequency = config[CONF_FREQUENCY]
    if not cg.is_template(frequency):
        frequency = int(round(frequency))
    template_ = await cg.templatable(frequency, args, cg.uint32)
    cg.add(var.set_frequency(template_))
    return var


def validate_tolerance(value):
    if isinstance(value, dict):
        return TOLERANCE_SCHEMA(value)

    if "%" in str(value):
        type_ = TYPE_PERCENTAGE
    else:
        try:
            cv.positive_time_period_microseconds(value)
            type_ = TYPE_TIME
        except cv.Invalid as exc:
            raise cv.Invalid(
                "Tolerance must be a percentage or time. Configurations made before 2024.5.0 treated the value as a percentage."
            ) from exc

    return TOLERANCE_SCHEMA(
        {
            CONF_VALUE: value,
            CONF_TYPE: type_,
        }
    )

#MULTI_CONF will be possible once the cmt2300a code is refactored
#to use different spi pins for each instance
#MULTI_CONF = True
CONFIG_SCHEMA = remote_base.validate_triggers(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(TuyaRfComponent),
            cv.Optional(CONF_SCLK_PIN, default='P14'): cv.All(pins.internal_gpio_output_pin_schema),
            cv.Optional(CONF_MOSI_PIN, default='P16'): cv.All(pins.internal_gpio_output_pin_schema),
            cv.Optional(CONF_CSB_PIN, default='P6'): cv.All(pins.internal_gpio_output_pin_schema),
            cv.Optional(CONF_FCSB_PIN, default='P26'): cv.All(pins.internal_gpio_output_pin_schema),
            cv.Optional(CONF_TX_PIN, default='P20'): cv.All(pins.internal_gpio_output_pin_schema),
            cv.Optional(CONF_RX_PIN, default='P22'): cv.All(pins.internal_gpio_input_pin_schema),
            cv.Optional(CONF_RECEIVER_DISABLED, default=False): cv.boolean,
            cv.Optional(CONF_FREQUENCY, default="433.92MHz"): validate_frequency,
            cv.Optional(CONF_DUMP, default=[]): remote_base.validate_dumpers,
            cv.Optional(CONF_TOLERANCE, default="25%"): validate_tolerance,
            cv.Optional(CONF_BUFFER_SIZE, default="1000b"): cv.validate_bytes,
            cv.Optional(CONF_FILTER, default="50us"): cv.All(
                cv.positive_time_period_microseconds,
                cv.Range(max=TimePeriod(microseconds=4294967295)),
            ),
            cv.Optional(CONF_START_PULSE_MIN, default="6000us"): cv.All(
                cv.positive_time_period_microseconds,
                cv.Range(max=TimePeriod(microseconds=4294967295)),
            ),
            cv.Optional(CONF_START_PULSE_MAX, default="10000us"): cv.All(
                cv.positive_time_period_microseconds,
                cv.Range(max=TimePeriod(microseconds=4294967295)),
            ),
            cv.Optional(CONF_END_PULSE, default="50ms"): cv.All(
                cv.positive_time_period_microseconds,
                cv.Range(max=TimePeriod(microseconds=4294967295)),
            ),
        }
    ).extend(cv.COMPONENT_SCHEMA)
)

def validate_pulses(config):
    start_pulse_min=config[CONF_START_PULSE_MIN]
    start_pulse_max=config[CONF_START_PULSE_MAX]
    end_pulse=config[CONF_END_PULSE]
    if start_pulse_max < start_pulse_min:
        raise cv.Invalid("start_pulse_max must be greater than start_pulse_min")
    if end_pulse < start_pulse_max:
        raise cv.Invalid("end_pulse must be greater than start_pulse_max")

async def to_code(config):
    sclk_pin = await cg.gpio_pin_expression(config[CONF_SCLK_PIN])
    mosi_pin = await cg.gpio_pin_expression(config[CONF_MOSI_PIN])
    csb_pin = await cg.gpio_pin_expression(config[CONF_CSB_PIN])
    fcsb_pin = await cg.gpio_pin_expression(config[CONF_FCSB_PIN])
    rx_pin = await cg.gpio_pin_expression(config[CONF_RX_PIN])
    tx_pin = await cg.gpio_pin_expression(config[CONF_TX_PIN])
    var = cg.new_Pvariable(config[CONF_ID],sclk_pin,mosi_pin,csb_pin,fcsb_pin,tx_pin,rx_pin)
    #await cg.register_component(var, config)
    dumpers = await remote_base.build_dumpers(config[CONF_DUMP])
    for dumper in dumpers:
        cg.add(var.register_dumper(dumper))

    triggers = await remote_base.build_triggers(config)
    for trigger in triggers:
        cg.add(var.register_listener(trigger))
    await cg.register_component(var, config)

    cg.add(
        var.set_tolerance(
            config[CONF_TOLERANCE][CONF_VALUE], config[CONF_TOLERANCE][CONF_TYPE]
        )
    )
    cg.add(var.set_receiver_disabled(config[CONF_RECEIVER_DISABLED]))
    cg.add(var.set_buffer_size(config[CONF_BUFFER_SIZE]))
    cg.add(var.set_filter_us(config[CONF_FILTER]))
    cg.add(var.set_start_pulse_min_us(config[CONF_START_PULSE_MIN]))
    cg.add(var.set_start_pulse_max_us(config[CONF_START_PULSE_MAX]))
    cg.add(var.set_end_pulse_us(config[CONF_END_PULSE]))
    cg.add(var.set_initial_frequency(int(round(config[CONF_FREQUENCY]))))
    validate_pulses(config)
