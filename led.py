from machine import Pin, Timer

class LED:
    def __init__(self, port=2):
        self.led = Pin(port, Pin.OUT)
        self.timer2 = Timer(2)

    def on(self):
        self.led.value(0)

    def off(self):
        self.led.value(1)

    def toggle(self):
        self.led.value(not self.led.value())

    def start(self, hz=100):     # keep flashlight
        self.timer2.init(period=hz, mode=Timer.PERIODIC, callback=lambda t: self.toggle())

    def hold(self, ms=2000):     # turn on LED for a few moment
        self.led.value(0)
        self.timer2.init(period=ms, mode=Timer.PERIODIC, callback=lambda t: self.led.value(1))

    def end(self):              # end flashlight
        self.timer2.deinit()
        self.led.value(1)

    def blink(self, ms=500):     # flash one times
        self.led.value(0)
        self.timer2.init(period=ms, mode=Timer.ONE_SHOT, callback=lambda t: self.led.value(1))

led = LED(2)
