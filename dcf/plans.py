

DEFAULT_AMOUNT = 1e6
FIXED_RATE = 0.01


def flat(num, amount=DEFAULT_AMOUNT):
    return [amount] * int(num)


def bullet(num, amount=DEFAULT_AMOUNT):
    return [0.] * (int(num) - 1) + [amount]


def amortize(num, amount=DEFAULT_AMOUNT):
    return [amount / num] * int(num)


def annuity(num, amount=DEFAULT_AMOUNT, fixed_rate=FIXED_RATE):
    q = 1. + fixed_rate
    a = amount * (q - 1) / (q ** int(num) - 1)
    return list(a * q ** i for i in range(int(num)))


def consumer(num, amount=DEFAULT_AMOUNT, fixed_rate=FIXED_RATE):
    total = amount * (1 + num * fixed_rate)
    return [total / num] * int(num)


