from machine import PWM, Pin, Timer
from led import led


class SG90:
    def __init__(self, port=12, min=15, max=130, on=15, off=80):
        self.MIN = min
        self.MAX = max
        self.ON = on
        self.OFF = off
        self.pwm0 = PWM(Pin(port), 50)
        self.timer1 = Timer(1)
        self.off()

    def fallback(self, cb, ms=1000):
        self.timer1.init(period=ms, mode=Timer.ONE_SHOT, callback=lambda t: cb())

    def set(self, n):
        led.on()
        self.pwm0.duty(n)
        self.fallback(self.de)

    def de(self):
        led.end()
        led.off()
        self.pwm0.deinit()
        self.timer1.deinit()

    def minn(self):
        self.set(self.MIN)

    def maxx(self):
        self.set(self.MAX)

    def on(self, ms=1500):
        led.start()
        self.pwm0.duty(self.ON)
        self.fallback(self.off, ms)

    def off(self):
        self.pwm0.duty(self.OFF)
        self.fallback(self.de, ms=500)
