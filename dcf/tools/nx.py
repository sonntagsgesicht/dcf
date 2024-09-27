


def simple_bracketing(func, a, b, precision=1e-13):
    """ find root by _simple_bracketing an interval

    :param callable func: function to find root
    :param float a: lower interval boundary
    :param float b: upper interval boundary
    :param float precision: max accepted error
    :rtype: float
    :return: :code:`m` of last recursion step
        with :code:`m = a + (b-a) *.5`

    """
    fa, fb = func(a), func(b)
    if fb < fa:
        f = (lambda x: -func(x))
        fa, fb = fb, fa
    else:
        f = func

    if not fa <= 0. <= fb:
        msg = "_simple_bracketing function must be loc monotone " \
              f"between {a:0.4f} and {b:0.4f}\n" \
              f"and 0.0 between  {fa:0.4f} and {fb:0.4f}."
        raise AssertionError(msg)

    m = a + (b - a) * 0.5
    if abs(b - a) < precision and abs(fb - fa) < precision:
        return m

    a, b = (m, b) if f(m) < 0 else (a, m)
    return simple_bracketing(f, a, b, precision)
