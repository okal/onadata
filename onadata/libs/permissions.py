from collections import defaultdict
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import (
    assign_perm,
    remove_perm,
    get_users_with_perms)
from onadata.apps.api.models import OrganizationProfile
from onadata.apps.main.models.user_profile import UserProfile
from onadata.apps.logger.models import XForm
from onadata.apps.api.models import Project

CAN_ADD_XFORM_TO_PROFILE = 'can_add_xform'
CAN_VIEW_ORGANIZATION_PROFILE = 'view_organizationprofile'
CAN_VIEW_PROFILE = 'view_profile'
CAN_CHANGE_XFORM = 'change_xform'
CAN_ADD_XFORM = 'add_xform'
CAN_DELETE_XFORM = 'delete_xform'
CAN_VIEW_XFORM = 'view_xform'
CAN_ADD_SUBMISSIONS = 'report_xform'
CAN_TRANSFER_OWNERSHIP = 'transfer_xform'
CAN_MOVE_TO_FOLDER = 'move_xform'

# Project Permissions
CAN_VIEW_PROJECT = 'view_project'
CAN_CHANGE_PROJECT = 'change_project'
CAN_TRANSFER_PROJECT_OWNERSHIP = 'transfer_project'
CAN_DELETE_PROJECT = 'delete_project'


class Role(object):
    class_to_permissions = None
    permissions = None
    name = None

    @classmethod
    def _remove_obj_permissions(self, user, obj):
        content_type = ContentType.objects.get(
            model=obj.__class__.__name__.lower(),
            app_label=obj.__class__._meta.app_label
        )
        object_permissions = user.userobjectpermission_set.filter(
            object_pk=obj.pk, content_type=content_type)

        for perm in object_permissions:
            remove_perm(perm.permission.codename, user, obj)

    @classmethod
    def add(cls, user, obj):
        cls._remove_obj_permissions(user, obj)

        for codename, klass in cls.permissions:
            if isinstance(obj, klass):
                assign_perm(codename, user, obj)

    @classmethod
    def has_role(cls, permissions, obj):
        """Check that permission correspond to this role for this object.

        :param permissions: A list of permissions.
        :param obj: An object to get the permissions of.
        """
        return set(permissions) == set(cls.class_to_permissions[type(obj)])

    @classmethod
    def user_has_role(cls, user, obj):
        """Check that a user has this role.

        :param user: A user object.
        :param obj: An object to get the permissions of.
        """
        return user.has_perms(cls.class_to_permissions[type(obj)], obj)


class ReadOnlyRole(Role):
    name = 'readonly'
    permissions = (
        (CAN_VIEW_ORGANIZATION_PROFILE, OrganizationProfile),
        (CAN_VIEW_XFORM, XForm),
        (CAN_VIEW_PROJECT, Project),
    )


class DataEntryRole(Role):
    name = 'dataentry'
    permissions = (
        (CAN_ADD_SUBMISSIONS, XForm),
        (CAN_ADD_XFORM, Project),
        (CAN_VIEW_ORGANIZATION_PROFILE, OrganizationProfile),
        (CAN_VIEW_PROJECT, Project),
        (CAN_VIEW_XFORM, XForm),
    )


class EditorRole(Role):
    name = 'editor'
    permissions = (
        (CAN_ADD_SUBMISSIONS, XForm),
        (CAN_ADD_XFORM, Project),
        (CAN_CHANGE_PROJECT, Project),
        (CAN_CHANGE_XFORM, XForm),
        (CAN_VIEW_ORGANIZATION_PROFILE, OrganizationProfile),
        (CAN_VIEW_PROJECT, Project),
        (CAN_VIEW_XFORM, XForm),
    )


class ManagerRole(Role):
    name = 'manager'
    permissions = (
        (CAN_ADD_XFORM, XForm),
        (CAN_ADD_XFORM_TO_PROFILE, OrganizationProfile),
        (CAN_ADD_XFORM_TO_PROFILE, UserProfile),
        (CAN_CHANGE_PROJECT, Project),
        (CAN_CHANGE_XFORM, XForm),
        (CAN_DELETE_PROJECT, Project),
        (CAN_VIEW_ORGANIZATION_PROFILE, OrganizationProfile),
        (CAN_VIEW_PROFILE, UserProfile),
        (CAN_VIEW_PROJECT, Project),
        (CAN_VIEW_XFORM, XForm),
    )


class OwnerRole(Role):
    name = 'owner'
    permissions = (
        (CAN_ADD_XFORM, Project),
        (CAN_ADD_XFORM, XForm),
        (CAN_ADD_XFORM_TO_PROFILE, OrganizationProfile),
        (CAN_ADD_XFORM_TO_PROFILE, UserProfile),
        (CAN_CHANGE_PROJECT, Project),
        (CAN_CHANGE_XFORM, XForm),
        (CAN_DELETE_PROJECT, Project),
        (CAN_DELETE_XFORM, XForm),
        (CAN_MOVE_TO_FOLDER, XForm),
        (CAN_TRANSFER_OWNERSHIP, XForm),
        (CAN_TRANSFER_PROJECT_OWNERSHIP, Project),
        (CAN_VIEW_ORGANIZATION_PROFILE, OrganizationProfile),
        (CAN_VIEW_PROFILE, UserProfile),
        (CAN_VIEW_PROJECT, Project),
        (CAN_VIEW_XFORM, XForm),
    )

ROLES = {role.name: role for role in [ReadOnlyRole,
                                      DataEntryRole,
                                      EditorRole,
                                      ManagerRole,
                                      OwnerRole]}

# Memoize a class to permissions dict.
for role in ROLES.values():
    role.class_to_permissions = defaultdict(list)
    [role.class_to_permissions[k].append(p) for p, k in role.permissions]


def get_role(permissions, obj):
    for role in ROLES.values():
        if role.has_role(permissions, obj):
            return role.name


def get_object_users_with_permissions(obj):
    """Returns users, roles and permissions for a object.
    """
    users_with_perms = []

    if obj:
        users_with_perms = [{
            'user': user,
            'role': get_role(permissions, obj),
            'permissions': permissions} for user, permissions in
            get_users_with_perms(obj,
                                 attach_perms=True,
                                 with_group_users=False).items()]

    return users_with_perms
