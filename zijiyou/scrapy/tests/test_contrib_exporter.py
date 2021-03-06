import unittest, cPickle as pickle
from cStringIO import StringIO

from scrapy.item import Item, Field
from scrapy.utils.python import str_to_unicode
from scrapy.utils.py26 import json
from scrapy.contrib.exporter import BaseItemExporter, PprintItemExporter, \
    PickleItemExporter, CsvItemExporter, XmlItemExporter, JsonLinesItemExporter, \
    JsonItemExporter

class TestItem(Item):
    name = Field()
    age = Field()


class BaseItemExporterTest(unittest.TestCase):

    def setUp(self):
        self.i = TestItem(name=u'John\xa3', age='22')
        self.output = StringIO()
        self.ie = self._get_exporter()

    def _get_exporter(self, **kwargs):
        return BaseItemExporter(**kwargs)

    def _check_output(self):
        pass

    def _assert_expected_item(self, exported_dict):
        for k, v in exported_dict.items():
            exported_dict[k] = str_to_unicode(v)
        self.assertEqual(self.i, exported_dict)

    def test_export_item(self):
        self.ie.start_exporting()
        try:
            self.ie.export_item(self.i)
        except NotImplementedError:
            if self.ie.__class__ is not BaseItemExporter:
                raise
        self.ie.finish_exporting()
        self._check_output()

    def test_serialize_field(self):
        self.assertEqual(self.ie.serialize_field( \
            self.i.fields['name'], 'name', self.i['name']), 'John\xc2\xa3')
        self.assertEqual( \
            self.ie.serialize_field(self.i.fields['age'], 'age', self.i['age']), '22')

    def test_fields_to_export(self):
        ie = self._get_exporter(fields_to_export=['name'])
        self.assertEqual(list(ie._get_serialized_fields(self.i)), [('name', 'John\xc2\xa3')])

        ie = self._get_exporter(fields_to_export=['name'], encoding='latin-1')
        name = list(ie._get_serialized_fields(self.i))[0][1]
        assert isinstance(name, str)
        self.assertEqual(name, 'John\xa3')

    def test_field_custom_serializer(self):
        def custom_serializer(value):
            return str(int(value) + 2)

        class CustomFieldItem(Item):
            name = Field()
            age = Field(serializer=custom_serializer)

        i = CustomFieldItem(name=u'John\xa3', age='22')

        ie = self._get_exporter()
        self.assertEqual(ie.serialize_field(i.fields['name'], 'name', i['name']), 'John\xc2\xa3')
        self.assertEqual(ie.serialize_field(i.fields['age'], 'age', i['age']), '24')


class PprintItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return PprintItemExporter(self.output, **kwargs)

    def _check_output(self):
        self._assert_expected_item(eval(self.output.getvalue()))


class PickleItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return PickleItemExporter(self.output, **kwargs)

    def _check_output(self):
        self._assert_expected_item(pickle.loads(self.output.getvalue()))


class CsvItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return CsvItemExporter(self.output, **kwargs)

    def _check_output(self):
        self.assertEqual(self.output.getvalue(), 'age,name\r\n22,John\xc2\xa3\r\n')

    def test_header(self):
        output = StringIO()
        ie = CsvItemExporter(output, fields_to_export=self.i.fields.keys())
        ie.start_exporting()
        ie.export_item(self.i)
        ie.finish_exporting()
        self.assertEqual(output.getvalue(), 'age,name\r\n22,John\xc2\xa3\r\n')

        output = StringIO()
        ie = CsvItemExporter(output, fields_to_export=['age'])
        ie.start_exporting()
        ie.export_item(self.i)
        ie.finish_exporting()
        self.assertEqual(output.getvalue(), 'age\r\n22\r\n')

        output = StringIO()
        ie = CsvItemExporter(output)
        ie.start_exporting()
        ie.export_item(self.i)
        ie.export_item(self.i)
        ie.finish_exporting()
        self.assertEqual(output.getvalue(), 'age,name\r\n22,John\xc2\xa3\r\n22,John\xc2\xa3\r\n')

        output = StringIO()
        ie = CsvItemExporter(output, include_headers_line=False)
        ie.start_exporting()
        ie.export_item(self.i)
        ie.finish_exporting()
        self.assertEqual(output.getvalue(), '22,John\xc2\xa3\r\n')


class XmlItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return XmlItemExporter(self.output, **kwargs)

    def _check_output(self):
        expected_value = '<?xml version="1.0" encoding="utf-8"?>\n<items><item><age>22</age><name>John\xc2\xa3</name></item></items>'
        self.assertEqual(self.output.getvalue(), expected_value)

    def test_multivalued_fields(self):
        output = StringIO()
        item = TestItem(name=[u'John\xa3', u'Doe'])
        ie = XmlItemExporter(output)
        ie.start_exporting()
        ie.export_item(item)
        ie.finish_exporting()
        expected_value = '<?xml version="1.0" encoding="utf-8"?>\n<items><item><name><value>John\xc2\xa3</value><value>Doe</value></name></item></items>'
        self.assertEqual(output.getvalue(), expected_value)

class JsonLinesItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return JsonLinesItemExporter(self.output, **kwargs)

    def _check_output(self):
        exported = json.loads(self.output.getvalue().strip())
        self.assertEqual(exported, dict(self.i))

class JsonItemExporterTest(JsonLinesItemExporterTest):

    def _get_exporter(self, **kwargs):
        return JsonItemExporter(self.output, **kwargs)

    def _check_output(self):
        exported = json.loads(self.output.getvalue().strip())
        self.assertEqual(exported, [dict(self.i)])

    def test_two_items(self):
        self.ie.start_exporting()
        self.ie.export_item(self.i)
        self.ie.export_item(self.i)
        self.ie.finish_exporting()
        exported = json.loads(self.output.getvalue())
        self.assertEqual(exported, [dict(self.i), dict(self.i)])

class CustomItemExporterTest(unittest.TestCase):

    def test_exporter_custom_serializer(self):
        class CustomItemExporter(BaseItemExporter):
            def serialize_field(self, field, name, value):
                if name == 'age':
                    return str(int(value) + 1)
                else:
                    return super(CustomItemExporter, self).serialize_field(field, \
                        name, value)

        i = TestItem(name=u'John', age='22')
        ie = CustomItemExporter()

        self.assertEqual( \
            ie.serialize_field(i.fields['name'], 'name', i['name']), 'John')
        self.assertEqual(
            ie.serialize_field(i.fields['age'], 'age', i['age']), '23')


if __name__ == '__main__':
    unittest.main()
