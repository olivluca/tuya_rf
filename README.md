# tuya_rf
Custom component to integrate a tuya rf433 hub into esphome.

The tuya device I'm using is a Moes ufo-r2-rf, it's both an IR and RF bridge.

It uses a [CBU module](https://docs.libretiny.eu/boards/cbu/) (BK7231N) and an [SH4 RF module](https://developer.tuya.com/en/docs/iot/sh4-module-datasheet?id=Ka04qyuydvubw) (which appears to be using a CMT2300A).

For more hardware details see [this forum post](https://www.elektroda.com/rtvforum/topic3975921.html).

There are several devices using the same CBU/SH4 combo.

My code is based on the remote_receiver/remote_transmitter components, adding the initialization sequence to put the CMT2300A in direct RX or TX mode.

The transmitter works, I got the codes using the original firmware and the tinytuya [RFRemoteControlDevice.py](https://github.com/jasonacox/tinytuya/blob/master/tinytuya/Contrib/RFRemoteControlDevice.py), the gencodes.py script uses the data to generate the `remote_transmitter.transmit_raw` codes.

The codes have been captured from a ceiling fan remote, the only rf remote I have.
I also used the codes dumped from the receiver to confirm that they also
work.

The receiver (both ir using the standard remote_receiver and rf using this component) should work once this [pull request](https://github.com/libretiny-eu/libretiny/pull/290) lands in libretiny.

For the IR part (to be used with the standard remote_receiver/remote_transmitter) the receiver is on P8 and the transmitter on P7.

Keep in mind that the CMT2300A cannot transmit and receive at the same time, so it is normally set in RX mode (unless the receiver has been disabled). To transmit a code the CMT2300A is switched
to TX mode, the code is sent, then it is switched back to RX mode (or to standby if the receiver has been disabled).

## rf filtering

The rf signal is quite noisy, so I do some filtering to receive the codes:

1. the starting pulse must be longer than 6ms but shorter than 10ms.
2. any time I see a starting pulse I discard the data and start again (usually the same code is sent more than once).
3. the pauses cannot last more than 6ms, if I see a pause longer than that I discard the data and start again.
4. the end pulse is around 90ms, I look for a pulse of at least 50ms to detect the end of the data.
5. if the end pulse never arrives, when the receiving buffer is about to overflow I discard the data and start again.

I don't know if these values are good only for my remote, but there are configuration variables to tune them.

## configuration variables

You can use the same configuration variables of the [remote_transmitter](https://esphome.io/components/remote_transmitter) and of the [remote_receiver](https://esphome.io/components/remote_receiver) (with the exception of the pin, here you can set the tx_pin and the rx_pin, but if you don't set them the defaults are used, idle also isn't used).

| variable | default | description |
|--|--|--|
|receiver_disabled|false|set it to true to disable the receiver|
|frequency|433.92MHz|rf frequency used both to transmit and receive, see [frequency](#frequency)|
|tx_pin|P20|pin used to transmit data, note that by default it is inverted, so a pulse is 1 and a space is 0 (the signal on my device is reversed: 0 for a pulse, 1 for a space)|
|rx_pin|P22|pin used to receive the data, note that by default it is inverted just like the tx_pin|
|start_pulse_min|6ms|the minimun duration of the starting pulse|
|start_pulse_max|10ms|the maximum duration of the starting pulse, must be greater than start_pulse_min|
|end_pulse|50ms|the minimum duration of the ending pulse, must be greater than start_pulse_max|
|sclk_pin|P14|clock of the spi communication with the CMT2300A. Only the number of the pin is used, the remaining parameters of the pin schema are ignored|
|mosi_pin|P16|the bidirectional data pin of the spi communication. Only the number of the pin is used, the remaining parameters of the pin schema are ignored|
|csb_pin|P6|spi chip select pin to read/write registers. Only the number of the pin is used, the remaining parameters of the pin schema are ignored|
|fcsb_pin|P26|spi chip select pin to read/write the fifo. It is not used|

## frequency

The CMT2300A can work in these bands: 126.33-170MHz, 189.5-340MHz, 379-510MHz and 758-1020MHz, the registers
are calculated following the CMOSTEK application note AN199 (rf frequency calculation guide) and they give
exactly the same values as the RFPDK tool.

Keep in mind that the antenna matching network on the board is optimized for 433.92MHz, so other frequencies
(e.g. 315MHz) should work but the range will probably be reduced.
The PA power registers are adjusted for the 280-340MHz band (values taken from an RFPDK 315MHz export),
the other bands use the same PA settings of 433.92MHz.

## actions

Since the receiver is mostly useful to learn new buttons, it's better to
leave it off and turn it on only when you want to start learning.
There are two actions, `tuya_rf.turn_on_receiver` (to turn the receiver on)
and `tuya_rf.turn_off_receiver` (to turn it off).
Once the code is fixed to work with multiple instances of tuya_rf (currently
it only allows one instance) you shuould specify the `receiver_id` in the
action.


The frequency can also be changed at runtime with the `tuya_rf.set_frequency` action
(the receiver, if active, is restarted on the new frequency):

```yaml
button:
  - platform: template
    name: "switch to 315MHz"
    on_press:
      - tuya_rf.set_frequency:
          frequency: 315MHz
```

`frequency` can also be a lambda returning the frequency in Hz.
