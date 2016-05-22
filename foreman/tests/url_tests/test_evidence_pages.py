"""
Tests to check that all pages work as expected with a 200 status code and not 404 or 500 for example.
"""

# local imports
from base_tester import URLTestCase

class EvidenceTestCase(URLTestCase):

    def test_disassociate_evidence(self):
        self._check_url('/cases/6/evidence/SCH-20140228-HDD_002/remove/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/6/evidence/6/remove/', None, 401)  # not logged in
        self._check_url('/cases/6/evidence/6/remove/', 1)  # login as admin
        self._check_url('/cases/6/evidence/6/remove/', 19, 403)  # login as a case manager
        self._check_url('/cases/6/evidence/6/remove/', 22)  # login as a case manager for case
        self._check_url('/cases/6/evidence/6/remove/', 10, 403)  # login as an investigator
        self._check_url('/cases/6/evidence/6/remove/', 6)  # login as an investigator for case
        self._check_url('/cases/6/evidence/6/remove/', 33, 403)  # login as a requester
        self._check_url('/cases/6/evidence/6/remove/', 32, 403)  # login as a requester for case

    def test_associate_evidence(self):
        self._check_url('/evidence/SCH-20140228-HDD_002/associate/', 1, 404)  # login as admin, but wrong case
        self._check_url('/evidence/4/associate/', None, 401)  # not logged in
        self._check_url('/evidence/4/associate/', 1)  # login as admin
        self._check_url('/evidence/4/associate/', 19)  # login as a case manager
        self._check_url('/evidence/4/associate/', 10)  # login as an investigator
        self._check_url('/evidence/4/associate/', 33, 403)  # login as a requester

        self._check_url('/evidence/6/associate/', 1, 404)  # login as admin
        self._check_url('/evidence/6/associate/', 19, 404)  # login as a case manager
        self._check_url('/evidence/6/associate/', 10, 404)  # login as an investigator
        self._check_url('/evidence/6/associate/', 33, 404)  # login as a requester

    def test_delete_evidence_photo(self):
        self._check_url('/evidence/1/uploads/1/delete/', None, 401)  # not logged in
        self._check_url('/evidence/1/uploads/1/delete/', 1)  # login as admin
        self._check_url('/evidence/1/uploads/1/delete/', 19, 403)  # login as a case manager
        self._check_url('/evidence/1/uploads/1/delete/', 10, 403)  # login as an investigator
        self._check_url('/evidence/1/uploads/1/delete/', 2)  # login as an investigator for this case
        self._check_url('/evidence/1/uploads/1/delete/', 33, 403)  # login as a requester
        self._check_url('/evidence/1/uploads/1/delete/', 18)  # login as a primary case manager for this case
        self._check_url('/evidence/1/uploads/1/delete/', 28, 403)  # login as a requester for this case

    def test_add_evidence_photo(self):
        self._check_url('/evidence/1/uploads/add/', None, 401)  # not logged in
        self._check_url('/evidence/1/uploads/add/', 1)  # login as admin
        self._check_url('/evidence/1/uploads/add/', 19, 403)  # login as a case manager
        self._check_url('/evidence/1/uploads/add/', 10, 403)  # login as an investigator
        self._check_url('/evidence/1/uploads/add/', 2)  # login as an investigator for this case
        self._check_url('/evidence/1/uploads/add/', 33, 403)  # login as a requester
        self._check_url('/evidence/1/uploads/add/', 18)  # login as a primary case manager for this case
        self._check_url('/evidence/1/uploads/add/', 28, 403)  # login as a requester for this case

    def test_view_evidence_photo(self):
        self._check_url('/evidence/1/uploads/1/', None, 401)  # not logged in
        self._check_url('/evidence/1/uploads/1/', 1)  # login as admin
        self._check_url('/evidence/1/uploads/1/', 19)  # login as a case manager
        self._check_url('/evidence/1/uploads/1/', 10)  # login as an investigator
        self._check_url('/evidence/1/uploads/1/', 2)  # login as an investigator for this case
        self._check_url('/evidence/1/uploads/1/', 33, 403)  # login as a requester
        self._check_url('/evidence/1/uploads/1/', 25)  # login as a primary case manager for this case
        self._check_url('/evidence/1/uploads/1/', 28)  # login as a requester for this case

    def test_view_all_evidence(self):
        self._check_url('/evidence/', None, 401)  # not logged in
        self._check_url('/evidence/', 1)  # login as admin
        self._check_url('/evidence/', 19)  # login as a case manager
        self._check_url('/evidence/', 1)  # login as an investigator
        self._check_url('/evidence/', 7)  # login as a QA
        self._check_url('/evidence/', 33, 403)  # login as a requester

    def test_custody_check_in(self):
        self._check_url('/evidence/9/custody/check-in/', None, 401)  # not logged in
        self._check_url('/evidence/9/custody/check-in/', 1, 404)  # login as admin
        self._check_url('/evidence/9/custody/check-in/', 19, 404)  # login as a case manager
        self._check_url('/evidence/9/custody/check-in/', 10, 404)  # login as an investigator
        self._check_url('/evidence/9/custody/check-in/', 9, 404)  # login as an investigator for this case
        self._check_url('/evidence/9/custody/check-in/', 33, 404)  # login as a requester
        self._check_url('/evidence/9/custody/check-in/', 25, 404)  # login as a primary case manager for this case
        self._check_url('/evidence/9/custody/check-in/', 35, 404)  # login as a requester for this case

        self._check_url('/evidence/5/custody/check-in/', 1)  # login as admin
        self._check_url('/evidence/5/custody/check-in/', 19, 403)  # login as a case manager
        self._check_url('/evidence/5/custody/check-in/', 22)  # login as a case manager for this case
        self._check_url('/evidence/5/custody/check-in/', 6)  # login as an investigator for this case
        self._check_url('/evidence/5/custody/check-in/', 9, 403)  # login as an investigator

    def test_custody_check_out(self):
        self._check_url('/evidence/9/custody/check-out/', None, 401)  # not logged in
        self._check_url('/evidence/9/custody/check-out/', 1)  # login as admin
        self._check_url('/evidence/9/custody/check-out/', 19, 403)  # login as a case manager
        self._check_url('/evidence/9/custody/check-out/', 10, 403)  # login as an investigator
        self._check_url('/evidence/9/custody/check-out/', 9)  # login as an investigator for this case
        self._check_url('/evidence/5/custody/check-out/', 6, 404)  # login as an investigator for this case
        self._check_url('/evidence/9/custody/check-out/', 33, 403)  # login as a requester
        self._check_url('/evidence/9/custody/check-out/', 25)  # login as a primary case manager for this case
        self._check_url('/evidence/9/custody/check-out/', 35, 403)  # login as a requester for this case

    def test_view_evidence(self):
        self._check_url('/cases/testing/evidence/SCH-20140228-HDD_002/', 1, 404)  # login as admin, but wrong case
        self._check_url('/cases/9/evidence/testing/', 1, 404)  # login as admin, but wrong evidence
        self._check_url('/cases/9/evidence/9/', None, 401)  # not logged in
        self._check_url('/cases/9/evidence/9/', 1)  # login as admin
        self._check_url('/cases/9/evidence/9/', 19, 403)  # login as a case manager
        self._check_url('/cases/9/evidence/9/', 10, 403)  # login as an investigator
        self._check_url('/cases/9/evidence/9/', 9)  # login as an investigator for this case
        self._check_url('/cases/9/evidence/9/', 33, 403)  # login as a requester
        self._check_url('/cases/9/evidence/9/', 25)  # login as a primary case manager for this case
        self._check_url('/cases/9/evidence/9/', 35)  # login as a requester for this case

    def test_view_evidence_caseless(self):
        self._check_url('/evidence/testing/', 1, 404)  # login as admin, but wrong evidence
        self._check_url('/evidence/4/', None, 401)  # not logged in
        self._check_url('/evidence/4/', 1)  # login as admin
        self._check_url('/evidence/4/', 19)  # login as a case manager
        self._check_url('/evidence/4/', 10)  # login as an investigator
        self._check_url('/evidence/4/', 33, 403)  # login as a requester

    def test_edit_evidence(self):
        self._check_url('/evidence/SCH-20140228-HDD_002/edit/', 1, 404)  # login as admin, but wrong case
        self._check_url('/evidence/9/edit/', None, 401)  # not logged in
        self._check_url('/evidence/9/edit/', 1)  # login as admin
        self._check_url('/evidence/9/edit/', 19, 403)  # login as a case manager
        self._check_url('/evidence/9/edit/', 25)  # login as a primary case manager for this case
        self._check_url('/evidence/9/edit/', 10, 403)  # login as an investigator
        self._check_url('/evidence/9/edit/', 9)  # login as a primary investigator for this case
        self._check_url('/evidence/9/edit/', 33, 403)  # login as a requester

    def test_edit_evidence_caseless(self):
        self._check_url('/evidence/SCH-20140228-HDD_001/edit/', 1, 404)  # login as admin, but wrong case
        self._check_url('/evidence/4/edit/', None, 401)  # not logged in
        self._check_url('/evidence/4/edit/', 1)  # login as admin
        self._check_url('/evidence/4/edit/', 19)  # login as a case manager
        self._check_url('/evidence/4/edit/', 10)  # login as an investigator
        self._check_url('/evidence/4/edit/', 33, 403)  # login as a requester

    def test_add_evidence(self):
        self._check_url('/cases/9/evidence/add/', None, 401)  # not logged in
        self._check_url('/cases/9/evidence/add/', 1)  # login as admin
        self._check_url('/cases/9/evidence/add/', 19, 403)  # login as a case manager
        self._check_url('/cases/9/evidence/add/', 11, 403)  # login as an investigator
        self._check_url('/cases/9/evidence/add/', 33, 403)  # login as a requester
        self._check_url('/cases/9/evidence/add/', 25)  # login as a primary case manager for this case
        self._check_url('/cases/9/evidence/add/', 6)  # login as a primary investigator for this case
        self._check_url('/cases/9/evidence/add/', 7)  # login as a secondary investigator for this case
        self._check_url('/cases/9/evidence/add/', 35, 403)  # login as a requester for this case

    def test_add_evidence_caseless(self):
        self._check_url('/evidence/add/', None, 401)  # not logged in
        self._check_url('/evidence/add/', 1)  # login as admin
        self._check_url('/evidence/add/', 19)  # login as a case manager
        self._check_url('/evidence/add/', 11)  # login as an investigator
        self._check_url('/evidence/add/', 33, 403)  # login as a requester

    def test_remove_evidence_caseless(self):
        self._check_url('/evidence/4/remove/', None, 401)  # not logged in
        self._check_url('/evidence/4/remove/', 1)  # login as admin
        self._check_url('/evidence/4/remove/', 19)  # login as a case manager
        self._check_url('/evidence/4/remove/', 7, 403)  # login as an investigator
        self._check_url('/evidence/4/remove/', 35, 403)  # login as a requester

    def test_destroy_evidence(self):
        self._check_url('/evidence/7/destroy/', None, 401)  # not logged in
        self._check_url('/evidence/7/destroy/', 1)  # login as admin
        self._check_url('/evidence/7/destroy/', 19, 403)  # login as a case manager
        self._check_url('/evidence/7/destroy/', 24)  # login as a case manager for this case
        self._check_url('/evidence/7/destroy/', 8)  # login as an investigator for this case
        self._check_url('/evidence/7/destroy/', 9, 403)  # login as an investigator
        self._check_url('/evidence/7/destroy/', 35, 403)  # login as a requester
