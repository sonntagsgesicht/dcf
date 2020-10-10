# -*- coding: utf-8 -*-

# dcf
# ---
# A Python library for generating discounted cashflows.
# 
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.4, copyright Saturday, 10 October 2020
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)


from unittest import TestCase

from dcf.ratingclass import RatingClass


class RatingClassUnitTest(TestCase):
    def _test_rating_class_without_master_scale(self):
        self.assertRaises(TypeError, RatingClass, '*')

        r = RatingClass(masterscale=('A', 'B', 'C', 'D'))
        self.assertRaises(ValueError, list, r)

        r = RatingClass(0.2)
        self.assertEqual(repr(r), 'RatingClass(0.2000000)')
        self.assertEqual(str(r), repr(r))
        self.assertEqual(r.masterscale, None)
        self.assertEqual(list(r), [])

    def _test_rating_class_with_master_scale(self):
        r = RatingClass(value=0.000001, masterscale=('A', 'B', 'C', 'D'))
        self.assertAlmostEqual(float(r), 0.000001)
        self.assertRaises(ValueError, list, r)

        r = RatingClass(value=0.3, masterscale=('A', 'B', 'C', 'D'))
        self.assertAlmostEqual(float(r), 0.3)
        self.assertAlmostEqual(list(r), [0., 0., 0.7777778, 0.2222222])
        self.assertEqual('0.7777778 C + 0.2222222 D', str(r))
        self.assertEqual('[' + str(r) + ']-RatingClass(0.3000000)', repr(r))

        self.assertEqual(len(list(r)), len(r.masterscale))
        self.assertAlmostEqual(sum(list(r)), 1.)
        self.assertAlmostEqual(min(list(r)), 0.)

        r = RatingClass(value='A', masterscale=('A', 'B', 'C', 'D'))
        self.assertAlmostEqual(0.001, float(r))
        for k, v in list(r.masterscale.items()):
            self.assertAlmostEqual(v, float(RatingClass(k, r.masterscale)))

        self.assertRaises(TypeError, RatingClass, 'X', r.masterscale)

    def _test_sloppy_rating_class_with_master_scale(self):
        RatingClass.SLOPPY = True
        r = RatingClass(-0.001, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([-1.0, 0.0, 0.0, 0.0], list(r))
        r = RatingClass(0.0, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([0.0, 0.0, 0.0, 0.0], list(r))
        r = RatingClass(0.000001, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([0.001, 0.0, 0.0, 0.0], list(r))
        r = RatingClass(0.5, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([0.0, 0.0, 0.5555556, 0.4444444], list(r))
        r = RatingClass(2.0, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual([0.0, 0.0, 0.0, 2.0], list(r))

    def _test_master_scale_rating_classes(self):
        r = RatingClass(value=0.3, masterscale=('A', 'B', 'C', 'D'))
        self.assertEqual(list(r.masterscale.keys()), ['A', 'B', 'C', 'D'])
        self.assertEqual(str(r.masterscale), '[[A]-RatingClass(0.0010000), '
                                             '[B]-RatingClass(0.0100000), '
                                             '[C]-RatingClass(0.1000000), '
                                             '[D]-RatingClass(1.0000000)]')
        self.assertEqual(repr(r.masterscale), 'master_scale('
                                              '[A]-RatingClass(0.0010000), '
                                              '[B]-RatingClass(0.0100000), '
                                              '[C]-RatingClass(0.1000000), '
                                              '[D]-RatingClass(1.0000000))')

        for y, z in list(r.masterscale.items()):
            x = RatingClass(z, r.masterscale)
            self.assertEqual(str(x), y)
            self.assertEqual(repr(x), '[%s]-RatingClass(%.7f)' % (y, z))

        for i, (x, y) in enumerate(r.masterscale.items()):
            self.assertAlmostEqual(10 ** (len(r.masterscale) - i) * y, 10)
            vec = list(RatingClass(y, r.masterscale))
            self.assertEqual(vec.pop(i), 1.)
            self.assertAlmostEqual(max(vec), 0.)
            self.assertAlmostEqual(min(vec), 0.)

        for k in r.masterscale:
            r.masterscale[k] = -1.
        self.assertEqual(list(r.masterscale.values()), [-1.] * len(r.masterscale))
