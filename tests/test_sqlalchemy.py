import unittest
import pytest
import datetime
import pdb
from flask import Flask, jsonify, json
from flask_jsontools import (
    jsonapi,
    JsonResponse,
    FlaskJsonClient,
    JsonSerializableBase,
    DynamicJSONEncoder,
    SqlAlchemyResponse
)
from sqlalchemy.ext.serializer import loads, dumps
from sqlalchemy.orm import (
    relationship,
    sessionmaker,
    subqueryload,
)
from sqlalchemy import (
    select,
    create_engine,
    MetaData,
    inspect,
)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import (
        Table,
        Column,
        Integer,
        String,
        ForeignKey,
        Text,
        DateTime,
        SmallInteger,
        PrimaryKeyConstraint
)



Base = declarative_base(cls=(JsonSerializableBase,))


class Person(Base):
    __tablename__ = 'person'
    _json_exclude = ['id', 'birth']
    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    birth = Column(DateTime)
    cats = relationship('Cat')

    def __init__(self, name):
        self.name = name
        self.birth = datetime.datetime.utcnow()


class Cat(Base):
    __tablename__ = 'cat'
    _json_exclude = ['toy']
    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    toy = Column(String(256))
    person_id = Column(Integer, ForeignKey('person.id'))

    def __init__(self, name):
        self.name = name


class ModelTest(unittest.TestCase):

    def setUp(self):
        #config flask
        self.app = app = Flask(__name__)
        #self.json_encoder = DynamicJSONEncoder
        self.app.test_client_class = FlaskJsonClient
        self.app.debug = self.app.testing = True

        #config sqlalchemy
        self.engine = create_engine('sqlite://')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

        #add some data

        pookey = Cat('pookey')
        toonses = Cat('toonses')
        spaz = Cat('spaz')

        self.session.add(pookey)
        self.session.add(toonses)
        self.session.add(spaz)

        oman = Person('oman')
        twoman = Person('twoman')

        self.session.add(oman)
        self.session.add(twoman)

        oman.cats.append(pookey)
        oman.cats.append(toonses)

        twoman.cats.append(spaz)

        self.session.commit()

        # Views
        @app.route('/persons', methods=['GET'])
        def persons():
            rs = self.session.query(Person).all()
            return SqlAlchemyResponse(rs)

        @app.route('/person', methods=['GET'])
        def person():
            rs = self.session.query(Person).first()
            return SqlAlchemyResponse(rs)

    def test_model_json_dumps(self):
        '''
        we test with and without the relationship cats.
        relationship must be called out with subqueryload
        http://docs.sqlalchemy.org/en/rel_0_9/orm/loading_relationships.html

        using the DynamicJSONEncoder via the json.dumps
        testing if this will follow the subresults
        '''

        rs_oman = self.session.query(Person) \
                .options(subqueryload(Person.cats)) \
                .filter(Person.name == 'oman')
        x = json.loads(json.dumps(rs_oman.first(), cls=DynamicJSONEncoder))
        self.assertSequenceEqual(x,
                                 {'cats': [{'id': 1, 'name': 'pookey', 'person_id': 1}, \
                                           {'id': 2, 'name': 'toonses', 'person_id': 1}], \
                                  'name': 'oman'})

        rs_oman_again = self.session.query(Person) \
                .filter(Person.name == 'oman')
        v = json.loads(json.dumps(rs_oman_again.first(), cls=DynamicJSONEncoder))
        self.assertSequenceEqual(v, {'name': 'oman'})

        rs_twoman = self.session.query(Person) \
                .options(subqueryload(Person.cats)) \
                .filter(Person.name == 'twoman')
        y = json.loads(json.dumps(rs_twoman.first(), cls=DynamicJSONEncoder))
        self.assertSequenceEqual(y,
                                 {'cats': [{'id': 3, 'name': 'spaz', 'person_id': 2}], \
                                  'name': 'twoman'})

    def test_model_json_first(self):
        expected = {'cats': [{'id': 1, 'name': 'pookey', 'person_id': 1}, {'id': 2, 'name': 'toonses', 'person_id': 1}], 'name': 'oman'}
        query = self.session.query(Person) \
                .options(subqueryload(Person.cats)) \
                .filter(Person.name == 'oman')

        rs = json.loads(DynamicJSONEncoder().encode(query.first()))
        self.assertSequenceEqual(rs, expected)

    def test_model_json_all(self):
        query = self.session.query(Person)
        rs = json.loads(DynamicJSONEncoder().encode(query.all()))
        self.assertSequenceEqual(rs, [{'name': 'oman'}, {'name': 'twoman'}])

    def test_model_asdict(self):
        '''
        a keyedtuple could be the result of a query
        need to call the _asdict method to get dictionary

         http://docs.sqlalchemy.org/en/latest/core/selectable.html
         '''

        empty = json.dumps('', cls=DynamicJSONEncoder)
        empty = json.dumps([], cls=DynamicJSONEncoder)

        query = select([Person.id, Person.name]) \
                .select_from(Person) \

        rs = self.session.query(query).first()

        dump = json.dumps(rs, cls=DynamicJSONEncoder)
        xray = json.loads(dump)
        self.assertSequenceEqual(xray, {'id': 1, 'name': 'oman'})

    def test_model_list_asdict(self):
        '''
        a keyedtuple could be the result of a query
        need to call the _asdict method to get dictionary

         http://docs.sqlalchemy.org/en/latest/core/selectable.html
         '''
        query = select([Person.id, Person.name]) \
                .select_from(Person) \

        rs = self.session.query(query).all()

        dump = json.dumps(rs, cls=DynamicJSONEncoder)
        xray = json.loads(dump)
        self.assertSequenceEqual(xray, [{'name': 'oman', 'id': 1}, {'name': 'twoman', 'id': 2}])

    def test_persons(self):
        with self.app.test_client() as c:
            rv = c.get('/persons')
            self.assertEqual(rv.status_code, 200)
            self.assertIsInstance(rv, JsonResponse)

            rv_json = rv.get_json()

            print(type(rv_json), rv_json)

            j = json.loads(rv_json)

            print('loads', type(j), j[0]['name'])

            self.assertEqual(j[0]['name'], 'oman')

    def test_person(self):
        with self.app.test_client() as c:
            rv = c.get('/person')
            self.assertEqual(rv.status_code, 200)
            self.assertIsInstance(rv, JsonResponse)

            rv_json = rv.get_json()

            print(type(rv_json), rv_json)

            j = json.loads(rv_json)

            print('loads', type(j), j['name'])

            self.assertEqual(j['name'], 'oman')
