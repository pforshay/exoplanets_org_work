from decimal import Decimal


def convert_to_jup(val):
    m = str(Decimal(val) / Decimal(317.83))
    r = str(Decimal(val) * Decimal(0.08921))
    print("Mass(J)= {0}, Radius(J)= {1}".format(m[:12], r[:12]))


def run():
    persist = True
    while persist:
        n = input("Enter a value in Earth units: ")
        if n == "q":
            persist = False
        else:
            convert_to_jup(n)


if __name__ == "__main__":
    run()
