from decimal import Decimal
import math


def calc_om(sin_om, cos_om):

    om = math.atan2(Decimal(sin_om), Decimal(cos_om))

    return math.degrees(om)


def run():
    persist = True
    while persist:
        sin_om = input("Enter sin(omega): ")
        cos_om = input("Enter cos(omega): ")
        om = calc_om(sin_om, cos_om)
        print("omega = {0}".format(om))


if __name__ == "__main__":
    run()
