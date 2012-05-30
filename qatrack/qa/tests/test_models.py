from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.client import Client
from django.test.utils import setup_test_environment
from django.utils import unittest,timezone

from django.contrib.auth.models import User
from qatrack.qa import models
from qatrack.units.models import Unit, UnitType, Modality

def create_basic_test(name,test_type=models.SIMPLE):

    cat = models.Category.objects.get(pk=1)

    unit = Unit.objects.get(pk=1)
    user = User.objects.get(pk=1)
    test = models.Test(
        name = name,
        short_name=name,
        description = "foo",
        type = test_type,
        category = cat,
        created_by = user,
        modified_by = user,
    )

    test.save()

    test_list = models.TestList(
        name="test list for %s" % name,
        slug="test list%s" % name,
        description="blah",
        active=True,
        created_by = user,
        modified_by = user,
    )
    test_list.save()

    membership = models.TestListMembership(test_list=test_list, test=test, order=1)
    membership.save()
    test_list.save()

    #get daily task list for unit
    utl = models.UnitTestLists.objects.get(
        unit = unit,
        frequency = models.DAILY,
    )

    utl.test_lists.add(test_list)
    utl.save()

    unit_test_info = models.UnitTestInfo.objects.get(
        unit=unit,
        test = test
    )

    return test, test_list, utl, unit_test_info

#============================================================================
class CycleTest(TestCase):
    """Test cases for cycles"""
    fixtures = [
        "test/units",
        "test/categories",
        "test/references",
        "test/tolerances",
        "test/users",
    ]
    NLISTS = 2
    #----------------------------------------------------------------------
    def setUp(self):

        self.user = User.objects.get(pk=1)
        cat = models.Category.objects.get(pk=1)

        test = models.Test(
            name = "test",
            short_name="test",
            description = "desc",
            type = models.SIMPLE,
            category = cat,
            created_by = self.user,
            modified_by = self.user,
        )

        test.save()

        for i in range(1,self.NLISTS+1):
            test_list = models.TestList(
                name="test %d"%i,
                slug="test %d"%i,
                description="blah",
                active=True,
                created_by = self.user,
                modified_by = self.user,
            )
            test_list.save()
            membership = models.TestListMembership(test_list=test_list,
                                test=test, order=1)
            membership.save()
            test_list.save()

        self.cycle = models.TestListCycle(name="test cycle")
        self.cycle.save()
        self.cycle.units = Unit.objects.all()
        self.cycle.save()
        test_lists = models.TestList.objects.all()

        for order,tl in enumerate(test_lists):
            membership = models.TestListCycleMembership(
                test_list = tl,
                order = order,
                cycle = self.cycle
            )
            membership.save()

    #----------------------------------------------------------------------
    def get_instance_for_test_list(self,test_list,unit):
        """"""
        instance = models.TestListInstance(
            test_list=test_list,
            unit=unit,
            created_by=self.user,
            modified_by=self.user
        )
        instance.save()

        for test in test_list.tests.all():
            test_instance = models.TestInstance(
                test=test,
                unit=unit,
                value=1.,
                skipped=False,
                test_list_instance=instance,
                reference = models.Reference.objects.get(pk=1),
                tolerance = models.Tolerance.objects.get(pk=1),
                status=models.UNREVIEWED,
                created_by=self.user,
                modified_by=self.user
            )
            test_instance.save()

        instance.save()
        return instance
    #----------------------------------------------------------------------
    def test_never_performed(self):
        unit = self.cycle.units.all()[0]
        self.assertIsNone(self.cycle.last_completed(unit))

    #----------------------------------------------------------------------
    def test_last_for_unit(self):

        unit = self.cycle.units.all()[0]
        test_list = self.cycle.first().test_list
        instance = self.get_instance_for_test_list(test_list,unit)
        membership = models.TestListCycleMembership.objects.get(
            cycle=self.cycle,order=0
        )
        self.assertEqual(membership,self.cycle.last_completed(unit))
    #----------------------------------------------------------------------
    def test_next_for_unit(self):

        unit = self.cycle.units.all()[0]

        #perform a full cycle ensuring a wrap
        nlist = self.cycle.test_lists.count()
        memberships = models.TestListCycleMembership.objects.filter(
            cycle=self.cycle
        ).order_by("order")

        for i, expected in enumerate(memberships):

            #get next to perform (on first cycle through we should get first list)
            next_ = self.cycle.next_for_unit(unit)
            self.assertEqual(next_, expected)

            #now perform the test list
            self.get_instance_for_test_list(next_.test_list,unit)

        #confirm that we have wrapped around to the beginning again
        next_ =  self.cycle.next_for_unit(unit)
        self.assertEqual(next_,memberships[0])

    #----------------------------------------------------------------------
    def test_length(self):
        self.assertEqual(self.NLISTS,len(self.cycle))


class UnitTestListTests(TestCase):

    fixtures = [
        "test/units",
        "test/categories",
        "test/references",
        "test/tolerances",
        "test/users",
    ]
    NLISTS = 2
    #----------------------------------------------------------------------
    def setUp(self):

        self.user = User.objects.get(pk=1)
        cat = models.Category.objects.get(pk=1)
        self.unit = Unit.objects.get(pk=1)

        self.test1 = models.Test(
            name = "test1",
            short_name="test1",
            description = "desc",
            type = models.SIMPLE,
            category = cat,
            created_by = self.user,
            modified_by = self.user,
        )

        self.test1.save()


        self.test2 = models.Test(
            name = "test2",
            short_name="test2",
            description = "desc",
            type = models.SIMPLE,
            category = cat,
            created_by = self.user,
            modified_by = self.user,
        )
        self.test2.save()

        self.test_list = models.TestList(
            name="test list",
            slug="test list",
            description="blah",
            active=True,
            created_by = self.user,
            modified_by = self.user,
        )
        self.test_list.save()
        membership = models.TestListMembership(test_list=self.test_list, test=self.test1, order=1)
        membership.save()
        self.test_list.save()

        #get daily task list for unit
        self.utl = models.UnitTestLists.objects.get(
            unit = self.unit,
            frequency = models.DAILY,
        )

        self.utl.save()
        self.utl.test_lists.add(self.test_list)
        self.utl.save()
    #----------------------------------------------------------------------
    def test_first_added(self):
        """"""
        unit_test_info = models.UnitTestInfo.objects.get(
            unit=self.unit,
            test = self.test1
        )
    #----------------------------------------------------------------------
    def test_add_to_existing(self):
        """"""
        membership = models.TestListMembership(
            test_list=self.test_list,
            test=self.test2,
            order=2
        )
        membership.save()
        self.test_list.save()

        unit_test_info = models.UnitTestInfo.objects.get(
            unit=self.unit,
            test = self.test2
        )


#============================================================================
class RefTolTests(TestCase):
    """make sure references/tolerance and pass/fail are operating correctly"""

    fixtures = [
        "test/units",
        "test/categories",
        "test/users",
    ]

    #----------------------------------------------------------------------
    def test_bool(self):
        test = models.Test(type=models.BOOLEAN)
        self.yes_ref = models.Reference(type = models.BOOLEAN,value = True,)
        self.no_ref = models.Reference(type = models.BOOLEAN,value = False,)

        self.bool_tol = models.Tolerance(
            type = models.ABSOLUTE,
            act_low =1E-10, tol_low =1E-10,
            tol_high=1E-10, act_high=1E-10,
        )

        yes_instance = models.TestInstance(value=1,test=test)
        no_instance = models.TestInstance(value=0,test=test)

        ok_tests = (
            self.bool_tol.test_instance(yes_instance,self.yes_ref),
            self.bool_tol.test_instance(no_instance,self.no_ref),
        )
        action_tests = (
            self.bool_tol.test_instance(no_instance,self.yes_ref),
            self.bool_tol.test_instance(yes_instance,self.no_ref),
        )
        for test in ok_tests:
            self.assertEqual(models.OK,test)
        for test in action_tests:
            self.assertEqual(models.ACTION,test)
    #----------------------------------------------------------------------
    def test_absolute(self):

        test = models.Test(type=models.SIMPLE)
        ti = models.TestInstance(test=test)
        ref = models.Reference(type=models.NUMERICAL,value=100.)
        tol = models.Tolerance(
            type=models.ABSOLUTE,
            act_low = -3,
            tol_low = -2,
            tol_high=  2,
            act_high=  3,
        )
        tests = (
            (models.ACTION,96),
            (models.ACTION,-100),
            (models.ACTION,1E99),
            (models.ACTION,103.1),
            (models.TOLERANCE,97),
            (models.TOLERANCE,97.5),
            (models.TOLERANCE,102.1),
            (models.TOLERANCE,103),
            (models.OK,100),
            (models.OK,102),
            (models.OK,98),
        )

        for result,val in tests:
            ti.value = val
            r = tol.test_instance(ti,ref)
            self.assertEqual(result,r)

    #----------------------------------------------------------------------
    def test_percent(self):

        test = models.Test(type=models.SIMPLE)
        ti = models.TestInstance(test=test)
        ref = models.Reference(type=models.NUMERICAL,value=100.)
        tol = models.Tolerance(
            type=models.PERCENT,
            act_low = -3,
            tol_low = -2,
            tol_high=  2,
            act_high=  3,
        )
        tests = (
            (models.ACTION,96),
            (models.ACTION,-100),
            (models.ACTION,1E99),
            (models.ACTION,103.1),
            (models.TOLERANCE,97),
            (models.TOLERANCE,97.5),
            (models.TOLERANCE,102.1),
            (models.TOLERANCE,103),
            (models.OK,100),
            (models.OK,102),
            (models.OK,98),
        )

        for result,val in tests:
            ti.value = val
            r = tol.test_instance(ti,ref)
            self.assertEqual(result,r)

    #----------------------------------------------------------------------
    def test_percent_diff_for_zero_ref(self):
        """A percent difference for a zero reference value doesn't make any sense
        Creating a UnitTestInfo object with a percent reference and zero value
        should fail.  Likewise, trying to calculate a percent difference for a
        zero based reference should raise a ValueError
        """

        tol = models.Tolerance(type=models.PERCENT,)
        with self.assertRaises(ValueError):
            tol.test_instance(
                models.TestInstance(test=models.Test(type=models.SIMPLE)),
                models.Reference(type=models.NUMERICAL,value=0)
            )

    #----------------------------------------------------------------------
    def test_create_unittestinfo_invalid(self):


        cat = models.Category.objects.get(pk=1)
        unit = Unit.objects.get(pk=1)
        user = User.objects.get(pk=1)
        test1 = models.Test(
            name = "test1",
            short_name="test1",
            description = "desc",
            type = models.SIMPLE,
            category = cat,
            created_by = user,
            modified_by = user,
        )

        test1.save()

        test_list = models.TestList(
            name="test list",
            slug="test list",
            description="blah",
            active=True,
            created_by = user,
            modified_by = user,
        )
        test_list.save()

        membership = models.TestListMembership(test_list=test_list, test=test1, order=1)
        membership.save()
        test_list.save()

        #get daily task list for unit
        utl = models.UnitTestLists.objects.get(unit = unit, frequency = models.DAILY,)
        utl.test_lists.add(test_list)
        utl.save()

        unit_test_info = models.UnitTestInfo.objects.get(
            unit=unit,
            test = test1
        )
        unit_test_info.reference = models.Reference(type=models.NUMERICAL,value=0)
        unit_test_info.tolerance = models.Tolerance(type=models.PERCENT)

        self.assertRaises(ValidationError,unit_test_info.clean)




#============================================================================
class TestTests(TestCase):
    fixtures = [
        "test/units",
        "test/categories",
        "test/references",
        "test/tolerances",
        "test/users",
    ]

    #----------------------------------------------------------------------
    def test_is_boolean(self):
        test = models.Test(type=models.BOOLEAN)
        self.assertTrue(test.is_boolean())

    #----------------------------------------------------------------------
    def test_set_references(self):
        test,test_list,utl, unit_test_info = create_basic_test("test")
        set_ref_link = test.set_references()
        self.client.login(username="testuser",password="password")
        import re
        for url in re.findall('href="(.*?)"',set_ref_link):
            response = self.client.get(url)
            self.assertEqual(response.status_code,200)

    #----------------------------------------------------------------------
    def test_unit_ref_tol(self):
        """"""
        test,test_list,utl, unit_test_info = create_basic_test("test")
        r = models.Reference.objects.get(pk=1)
        t = models.Tolerance.objects.get(pk=1)

        unit_test_info.reference = r
        unit_test_info.tolerance = t

        unit_test_info.save()
        self.assertListEqual(
            test.unit_ref_tol(utl.unit),
            [t.act_low,t.tol_low,r.value,t.tol_high,t.act_high]
        )

        unit_test_info.tolerance = None
        unit_test_info.save()
        self.assertListEqual(
            test.unit_ref_tol(utl.unit),
            [None, None,r.value, None, None]
        )

        unit_test_info.reference = None
        unit_test_info.save()
        self.assertListEqual(
            test.unit_ref_tol(utl.unit),
            [None, None,None, None, None]
        )

        unit_test_info.tolerance = t
        unit_test_info.save()
        self.assertListEqual(
            test.unit_ref_tol(utl.unit),
            [t.act_low,t.tol_low,None,t.tol_high,t.act_high]
        )

    #----------------------------------------------------------------------
    def test_invalid_calc_procedure(self):

        test = models.Test(type=models.SIMPLE)

        #don't need to check if not composite
        self.assertIsNone(test.clean_calculation_procedure())

        #calc procedure but test type not compsite
        test.calculation_procedure = "foo"
        self.assertRaises(ValidationError, test.clean_calculation_procedure)

        test.type = models.COMPOSITE

        #no result line defined
        self.assertRaises(ValidationError, test.clean_calculation_procedure)

        invalid_calc_procedures = (
            "resul t = a + b",
            "_result = a + b",
            "0result = a+b",
            " result = a + b",
            "result_=foo",
            "",
            "foo = a +b",
        )

        for icp in invalid_calc_procedures:
            test.calculation_procedure = icp
            try:
                msg = "Passed but should have failed:\n %s" % icp
                test.clean_calculation_procedure()
            except ValidationError:
                msg = ""
            self.assertTrue(len(msg)==0,msg=msg)

    #----------------------------------------------------------------------
    def test_valid_calc_procedure(self):
        test = models.Test(type=models.COMPOSITE)

        valid_calc_procedures = (
            "result = a + b",
            "result = 42",
            """foo = a + b
result = foo + bar""",
            """foo = a + b
result = foo + bar

    """
        )
        for vcp in valid_calc_procedures:
            test.calculation_procedure = vcp
            try:
                msg = ""
                test.clean_calculation_procedure()
            except ValidationError:
                msg = "Failed but should have passed:\n %s" % vcp
            self.assertTrue(len(msg)==0,msg=msg)
    #----------------------------------------------------------------------
    def test_constant_val(self):
        test = models.Test(type=models.SIMPLE)
        test.constant_value = 1
        self.assertRaises(ValidationError,test.clean_constant_value)

        test.constant_value = None
        test.type = models.CONSTANT
        self.assertRaises(ValidationError,test.clean_constant_value)

    #----------------------------------------------------------------------
    def test_short_name(self):

        test = models.Test(type=models.SIMPLE)
        invalid = ( "0 foo", "foo ", " foo" "foo bar", "foo*bar", "%foo", "foo$" )

        for i in invalid:
            test.short_name = i
            try:
                msg = "Short name should have failed but passed: %s" % i
                test.clean_short_name()
            except ValidationError:
                msg = ""

            self.assertTrue(len(msg)==0, msg=msg)

        valid = ("foo", "f6oo", "foo6","_foo","foo_","foo_bar",)
        for v in valid:
            test.short_name = v
            try:
                msg = ""
                test.clean_short_name()
            except ValidationError:
                msg = "Short name should have passed but failed: %s" % v
            self.assertTrue(len(msg)==0, msg=msg)
    #----------------------------------------------------------------------
    def test_clean_fields(self):
        test,test_list,utl, unit_test_info = create_basic_test("test")
        test.clean_fields()

    #----------------------------------------------------------------------
    def test_history(self):
        test,test_list,utl, unit_test_info = create_basic_test("test")
        td = timezone.timedelta
        now = timezone.now()

        #values purposely created out of order to make sure history
        #returns in correct order (i.e. ordered by date)
        history = [
            (now+td(days=4), 5, models.NO_TOL, models.UNREVIEWED),
            (now+td(days=1), 5, models.NO_TOL, models.UNREVIEWED),
            (now+td(days=3), 6, models.NO_TOL, models.UNREVIEWED),
            (now+td(days=2), 7, models.NO_TOL, models.UNREVIEWED),
        ]
        for wc, val, _, _ in history:
            tli = models.TestListInstance(
                test_list=test_list,
                unit=utl.unit,
                created_by=test.created_by,
                modified_by=test.created_by,
            )
            tli.work_completed = wc

            tli.save()
            ti1 = models.TestInstance(
                test=test,
                value=val,
                unit=utl.unit,
                test_list_instance = tli,
                created_by=test.created_by,
                modified_by=test.created_by,
                work_completed = wc
            )
            ti1.save()

        db_hist = test.history_for_unit(utl.unit)
        self.assertListEqual(sorted(history),db_hist)

        #test works correctly for just unit num
        db_hist = test.history_for_unit(utl.unit.number)
        self.assertListEqual(sorted(history),db_hist)

        #test returns correct number of results
        db_hist = test.history_for_unit(utl.unit.number,number=2)
        self.assertListEqual(sorted(history)[:2],db_hist)

#============================================================================
class TestTestList(TestCase):

    fixtures = [
        "test/units",
        "test/categories",
        "test/references",
        "test/tolerances",
        "test/users",
    ]

    #----------------------------------------------------------------------
    def test_last_completed(self):
        test,test_list,utl, unit_test_info = create_basic_test("test")
        td = timezone.timedelta
        now = timezone.now()
        last_completed_date = now+td(days=3)

        self.assertIsNone(test_list.last_completed_instance(utl.unit))

        #values purposely created out of order to make sure correct
        #last completed instance is returned correctly
        history = [
            (now+td(days=1), 5, models.NO_TOL, models.UNREVIEWED),
            (last_completed_date, 6, models.NO_TOL, models.UNREVIEWED),
            (now+td(days=2), 7, models.NO_TOL, models.UNREVIEWED),
        ]
        for wc, val, _, _ in history:
            tli = models.TestListInstance(
                test_list=test_list,
                unit=utl.unit,
                created_by=test.created_by,
                modified_by=test.created_by,
            )
            tli.work_completed = wc

            tli.save()
            ti1 = models.TestInstance(
                test=test,
                value=val,
                unit=utl.unit,
                test_list_instance = tli,
                created_by=test.created_by,
                modified_by=test.created_by,
                work_completed = wc
            )
            ti1.save()

        last = test_list.last_completed_instance(utl.unit)
        self.assertEqual(last.work_completed,last_completed_date)
    #----------------------------------------------------------------------
    def test_sublist(self):
        test,test_list,utl, unit_test_info = create_basic_test("test")
        sub_test,sub_test_list,sub_utl, sub_unit_test_info = create_basic_test("sub test")

        test_list.sublists.add(sub_test_list)
        test_list.save()
        self.assertListEqual([test,sub_test],test_list.all_tests())
    #----------------------------------------------------------------------
    def test_set_references(self):
        test,test_list,utl, unit_test_info = create_basic_test("test")
        set_ref_link = test_list.set_references()
        self.client.login(username="testuser",password="password")
        import re
        for url in re.findall('href="(.*?)"',set_ref_link):
            response = self.client.get(url)
            self.assertEqual(response.status_code,200)


#============================================================================
class TestNewUnitCreated(TestCase):
    fixtures = [
        "test/units",
        "test/categories",
        "test/references",
        "test/tolerances",
        "test/users",
    ]

    #----------------------------------------------------------------------
    def test_create(self):
        u = Unit(number=99,name="test unit")
        u.type = UnitType.objects.get(pk=1)
        u.save()
        u.modalities.add(Modality.objects.get(pk=1))
        u.save()

        utls = models.UnitTestLists.objects.filter(unit=u)
        freqs = utls.values_list("frequency",flat=True)
        self.assertSetEqual(set(freqs),set([x[0] for x in models.FREQUENCY_CHOICES]))
    #----------------------------------------------------------------------
    def test_retrieve_by_unit(self):
        unit = Unit.objects.get(pk=1)
        utls = models.UnitTestLists.objects.by_unit(unit).all()
        freqs = utls.values_list("frequency",flat=True)
        self.assertSetEqual(set(freqs),set([x[0] for x in models.FREQUENCY_CHOICES]))
    #----------------------------------------------------------------------
    def test_retrieve_by_frequency(self):
        all_units = set(Unit.objects.all())
        for freq,_ in models.FREQUENCY_CHOICES:
            utls = models.UnitTestLists.objects.by_frequency(freq).all()
            units = [x.unit for x in utls]
            self.assertSetEqual(set(units),all_units)
    #----------------------------------------------------------------------
    def test_retrieve_by_unit_frequency(self):
        u = Unit.objects.get(pk=1)
        freq = models.DAILY
        self.assertEqual(
            models.UnitTestLists.objects.by_unit_frequency(u,freq)[0].pk,
            models.UnitTestLists.objects.get(unit=u,frequency=freq).pk
        )

class TestUnitTestLists(TestCase):
    fixtures = [
        "test/units",
        "test/categories",
        "test/references",
        "test/tolerances",
        "test/users",
    ]

    #----------------------------------------------------------------------
    def test_due_date(self):
        test,test_list,utl, unit_test_info = create_basic_test("test")

        tli = models.TestListInstance(
            test_list=test_list,
            unit=utl.unit,
            created_by=test.created_by,
            modified_by=test.created_by,
        )
        tli.work_completed = timezone.now()

        tli.save()

        due = models.due_date(utl.unit,test_list)
        print due

if __name__ == "__main__":
    setup_test_environment()
    unittest.main()