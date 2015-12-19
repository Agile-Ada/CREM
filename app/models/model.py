from .. import db


# Associate multiple rooms to multiple events.
room_event = db.Table(
    'room_event',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('room_id', db.Integer, db.ForeignKey('room.id'))
)

# Associates multiple resources to multiple events.
event_resources = db.Table(
    'event_resources',
    db.Model.metadata,
    db.Column(
        'event_id',
        db.Integer(),
        db.ForeignKey('event.id', ondelete='CASCADE', onupdate='CASCADE')
    ),
    db.Column(
        'resource_id',
        db.Integer(),
        db.ForeignKey('resource.id', ondelete='CASCADE', onupdate='CASCADE')
    )
)

# Associates multiple persons to multiple events.
presenter_event = db.Table(
    'presenter_event',
    db.Column(
        'event_id',
        db.Integer,
        db.ForeignKey('event.id', ondelete='CASCADE', onupdate='CASCADE')
    ),
    db.Column(
        'presenter_id',
        db.Integer,
        db.ForeignKey('presenter.id', ondelete='CASCADE', onupdate='CASCADE')
    )
)

room_suitability = db.Table(
    'room_suitability',
    db.Column(
        'event_id',
        db.Integer,
        db.ForeignKey('event.id', ondelete='CASCADE', onupdate='CASCADE')
    ),
    db.Column(
        'room_id',
        db.Integer,
        db.ForeignKey('room.id', ondelete='CASCADE', onupdate='CASCADE')
    )
)

room_availability = db.Table(
    'room_availability',
    db.Column(
        'timeslot_id',
        db.Integer,
        db.ForeignKey('timeslot.id', ondelete='CASCADE', onupdate='CASCADE')
    ),
    db.Column(
        'room_id',
        db.Integer,
        db.ForeignKey('room.id', ondelete='CASCADE', onupdate='CASCADE')
    )
)


class Track(db.Model):
    __tablename__ = 'track'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    uid = db.Column(db.String(), unique=True)
    email = db.Column(db.String(), unique=True)
    trackhead_first_name = db.Column(db.String())
    trackhead_last_name = db.Column(db.String())
    active = db.Column(db.Boolean(), default=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.uid = email[:email.find('@')]

    def __repr__(self):
        return 'Track: %s' % self.name

    @property
    def names(self):
        """ Return only the names and uids of the tracks. """
        return {
            'name': self.name,
            'uid': self.uid
        }

    """
    The only reason CREM keeps staff email addresses in the
    database is so CREM can send emails. We will not
    include staff email addresses in any AJAX endpoints
    because all our staff understand each email
    begins with a track name, so they know how to contact
    each other already. Users = tracks = email addresses.
    If we expose them through an endpoint, the only value
    we provide would be for spam spiders to collect them.
    """


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    description = db.Column(db.String())
    comments = db.Column(db.String())
    active = db.Column(db.Boolean(), default=True)
    track_id = db.Column(db.Integer(), db.ForeignKey('track.id'))
    track = db.relationship('Track')
    rooms = db.relationship('Room',
                            secondary='room_event',
                            backref=db.backref('used_for_event'))
    eventtype_id = db.Column(db.Integer, db.ForeignKey('eventtype.id'))
    resources = db.relationship('Resource',
                                secondary=event_resources,
                                backref=db.backref('at_event'))
    players = db.Column(db.Integer())
    roundTables = db.Column(db.Integer())
    longTables = db.Column(db.Integer())
    facilityRequest = db.Column(db.String())
    presenters = db.relationship(
        'Presenter',
        secondary=presenter_event,
        backref=db.backref('at_event'),
        passive_deletes=True
    )
    timeslot_id = db.Column(db.Integer, db.ForeignKey('timeslot.id'))
    timeslot = db.relationship('Timeslot')
    duration = db.Column(db.Integer)  # The number of timeslots.
    convention_id = db.Column(db.Integer, db.ForeignKey('convention.id'))
    convention = db.relationship('Convention')
    fixed = db.Column(db.Boolean())

    def __repr__(self):
        return 'Event: %s' % self.title

    @property
    def useroutput(self):
        presenter_list = []
        for presenter in self.presenters:
            presenter_name = ('%s %s' % (presenter.first_name,
                                         presenter.last_name)).strip()
            presenter_list.append(presenter_name)

        # Create the string representing the start datetime.
        timeslot_duration = self.convention.timeslot_duration
        timeslot_index = self.timeslot.timeslot_index
        start_dt = self.convention.start_dt + timeslot_duration * timeslot_index
        if self.convention.datetime_format:
            start_dt_str = start_dt.strftime(self.convention.datetime_format)
        else:
            start_dt_str = start_dt.strftime('%m/%d/%Y %I:%M %p')

        return {
            'eventnumber': self.id,
            'title': self.title,
            'description': self.description,
            'comments': self.comments,
            'trackuid': self.track.uid,
            'track': self.track.name,
            'rooms': self.rooms,
            'event_type': self.event_type,
            'resources': self.resources,
            'presenters': ', '.join(presenter_list),
            'start': start_dt_str,
            'duration': self.duration
        }


class EventType(db.Model):
    __tablename__ = 'eventtype'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    active = db.Column(db.Boolean(), default=True)
    events = db.relationship('Event', backref='event_type')


class Presenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String())
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    phone = db.Column(db.String())
    active = db.Column(db.Boolean(), default=True)
    presentations = db.relationship(
        'Event',
        secondary=presenter_event,
        backref=db.backref('presented_by', passive_deletes=True)
    )

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return '%s %s (%s)' % (self.first_name, self.last_name, self.email)


class Resource(db.Model):
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    request_form_label = db.Column(db.String())
    displayed_on_requst_form = db.Column(db.Boolean())
    active = db.Column(db.Boolean(), default=True)

    def __init__(self, name, request_form_label, displayed_on_requst_form):
        self.name = name
        self.request_form_label = request_form_label
        self.displayed_on_requst_form = displayed_on_requst_form

    def __repr__(self):
        return 'Resource: %s' % self.name


class Room(db.Model):
    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(50))
    room_sq_ft = db.Column(db.Integer)
    room_capacity = db.Column(db.Integer)
    room_group_id = db.Column(db.Integer, db.ForeignKey('room_group.id'))
    room_group = db.relationship('RoomGroup', backref='rooms')
    convention_id = db.Column(db.Integer, db.ForeignKey('convention.id'))
    convention = db.relationship('Convention', backref='rooms')
    active = db.Column(db.Boolean(), default=True)
    suitable_events = db.relationship(
        'Event',
        secondary=room_suitability,
        backref=db.backref('suitable_rooms'),
        passive_deletes=True
    )
    available_timeslots = db.relationship(
        'Timeslot',
        secondary=room_availability,
        backref=db.backref('available_rooms'),
        passive_deletes=True
    )

    def __repr__(self):
        return 'Room: %s' % self.room_name

    @property
    def ui_rooms(self):
        return {
            'id': self.id,
            'name': self.room_name,
            'sq_ft': self.room_sq_ft,
            'capacity': self.room_capacity,
            'group_id': self.room_group_id,
            'suitable_events': self.suitable_events,
            'available_timeslots': self.available_timeslots
        }


class RoomGroup(db.Model):
    __tablename__ = 'room_group'
    id = db.Column(db.Integer, primary_key=True)
    room_group_name = db.Column(db.String(50))

    def __init__(self, room_group_name):
        self.room_group_name = room_group_name

    def __repr__(self):
        return 'Room Group: %s' % self.room_group_name

    @property
    def ui_room_groups(self):
        return {
            'id': self.id,
            'group_name': self.room_group_name,
        }


class Convention(db.Model):
    __tablename__ = 'convention'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    start_dt = db.Column(db.DateTime)
    end_dt = db.Column(db.DateTime)
    date_format = db.Column(db.String(50))
    datetime_format = db.Column(db.String(50))
    url = db.Column(db.String())
    timeslot_duration = db.Column(db.Interval())
    number_of_timeslots = db.Column(db.Integer)
    active = db.Column(db.Boolean(), default=True)

    def __repr__(self):
        return self.name

    @property
    def configs(self):
        return {
            'name': self.name,
            'start_dt': str(self.start_dt),
            'end_dt': str(self.end_dt),
            'timeslot_length': int(self.timeslot_duration.total_seconds() / 60),
            'number_of_timeslots': self.number_of_timeslots,
        }

class Timeslot(db.Model):
    __tablename__ = 'timeslot'
    id = db.Column(db.Integer(), primary_key=True)
    timeslot_index = db.Column(db.Integer(), unique=True)  # 0-based.
    name = db.Column(db.String())
    convention_id = db.Column(
        db.Integer(),
        db.ForeignKey('convention.id', ondelete='CASCADE', onupdate='CASCADE')
    )
    convention = db.relationship('Convention',
                                 backref=db.backref('timeslots'))
    rsvp_conflicts = db.Column(db.Integer())
    active = db.Column(db.Boolean(), default=True)

    def __init__(self, timeslot_index):
        self.timeslot_index = timeslot_index

    
