"""
    cloudplayer.api.model.user
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2018 by Nicolas Drebenstedt
    :license: GPL-3.0, see LICENSE for details
"""
import sqlalchemy as sql
import sqlalchemy.orm as orm

from cloudplayer.api.model import Base


class User(Base):

    __fields__ = [
        'id',
        'accounts',
        'created',
        'updated'
    ]
    __filters__ = []
    __mutable__ = []
    __public__ = [
        'id',
        'accounts'
    ]
    __table_args__ = (
        sql.PrimaryKeyConstraint(
            'id'),
    )

    id = sql.Column(sql.Integer)

    accounts = orm.relationship('Account', back_populates='user')
