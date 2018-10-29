from decimal import Decimal


def calc_t0(bjd, m0, per):
    t0 = str(Decimal(bjd) - ((Decimal(m0) / Decimal(360)) * Decimal(per)))
    print("T0= {0}".format(t0))


def run():
    persist = True
    bjd = None
    while persist:
        if not bjd:
            bjd = input("Enter BJD: ")
        m0 = input("Enter position at BJD: ")
        per = input("Enter period in days: ")
        if bjd == "q" or m0 == "q" or per == "q":
            persist = False
        else:
            calc_t0(bjd, m0, per)


if __name__ == "__main__":
    run()
