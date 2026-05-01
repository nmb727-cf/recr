from dataclasses import dataclass, field

from rest_framework.test import APIRequestFactory, force_authenticate


@dataclass(frozen=True)
class AccessCase:
    name: str
    method: str
    path: str
    view: object
    kwargs: dict = field(default_factory=dict)
    deny_roles: set[str] = field(default_factory=set)
    allow_roles: set[str] = field(default_factory=set)


class AccessMatrixMixin:
    """
    Reusable soft access-matrix harness.
    - deny_roles assertions are strict.
    - allow_roles assertions are optional and opt-in.
    """

    factory: APIRequestFactory
    users: dict

    def build_request(self, method: str, path: str):
        builder = getattr(self.factory, method.lower())
        return builder(path)

    def assert_matrix(self, cases: list[AccessCase]):
        for case in cases:
            for role, user in self.users.items():
                with self.subTest(case=case.name, role=role):
                    request = self.build_request(case.method, case.path)
                    force_authenticate(request, user=user)
                    response = case.view(request, **case.kwargs)

                    if role in case.deny_roles:
                        self.assertEqual(
                            response.status_code,
                            403,
                            msg=f"{case.name} should deny role={role}",
                        )
                    elif role in case.allow_roles:
                        self.assertNotEqual(
                            response.status_code,
                            403,
                            msg=f"{case.name} should allow role={role}",
                        )
