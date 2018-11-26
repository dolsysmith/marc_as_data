from pymarc.record import Record
from pymarc.exceptions import BaseAddressInvalid, RecordLeaderInvalid, \
		BaseAddressNotFound, RecordDirectoryInvalid, NoFieldsFound, \
		FieldNotFound
from pymarc.constants import LEADER_LEN, DIRECTORY_ENTRY_LEN, END_OF_RECORD
from pymarc.field import Field, SUBFIELD_INDICATOR, END_OF_FIELD, \
		map_marc8_field, RawField
from pymarc.marc8 import marc8_to_unicode
import re
import logging

class VGR_Record(Record):

	def decode_marc(self, marc, to_unicode=True, force_utf8=False, hide_utf8_warnings=False, utf8_handling='ignore'):

		self.leader = marc[0:LEADER_LEN]
		if len(self.leader) != LEADER_LEN:
			raise RecordLeaderInvalid
		if self.leader[9] == 'a' or self.force_utf8:
			encoding = 'utf-8'
		else:
			encoding = 'iso8859-1'
	
		base_address = int(marc[12:17])
		if base_address <= 0:
			raise BaseAddressNotFound
		if base_address >= len(marc):
			raise BaseAddressInvalid
	
		directory = marc[LEADER_LEN:base_address-1]

		if len(directory) % DIRECTORY_ENTRY_LEN != 0:
			raise RecordDirectoryInvalid
		field_total = len(directory) / DIRECTORY_ENTRY_LEN 
	
		field_count = 0
		while field_count < field_total:
			entry_start = field_count * DIRECTORY_ENTRY_LEN
			entry_end = entry_start + DIRECTORY_ENTRY_LEN
			entry = directory[entry_start:entry_end]
			entry_tag = entry[0:3]
			entry_length = int(entry[3:7])
			entry_offset = int(entry[7:12])
			entry_data = marc[base_address + entry_offset : base_address + entry_offset + entry_length - 1]
		
			if entry_tag < '010' and entry_tag.isdigit(): 
				if to_unicode:
					field = Field(tag=entry_tag, data=entry_data)
				else:
					field = RawField(tag=entry_tag, data=entry_data)
			else:
				subfields = list()
				subs = entry_data.split(SUBFIELD_INDICATOR)
			#subs = entry_data.split(SUBFIELD_INDICATOR.encode().decode('ascii', errors='ignore'))
				first_indicator = second_indicator = ' '
			#subs[0] = subs[0].decode('ascii')
				if len(subs[0]) == 0:
					logging.warning("missing indicators: %s", entry_data)
					first_indicator = second_indicator = ' '
				elif len(subs[0]) == 1:
					logging.warning("only 1 indicator found: %s", entry_data)
					first_indicator = subs[0][0]
					second_indicator = ' '
				elif len(subs[0]) > 2:
					logging.warning("more than 2 indicators found: %s", entry_data)
					first_indicator = subs[0][0]
					second_indicator = subs[0][1]
				else:
					first_indicator = subs[0][0]
					second_indicator = subs[0][1]
				for subfield in subs[1:]:
					if len(subfield) == 0:
						continue
					code = subfield[0:1]
					data = subfield[1:]
					if to_unicode:
						if self.leader[9] == 'a' or force_utf8:
							data = data.encode().decode('utf-8', utf8_handling)
						else: 
							data = marc8_to_unicode(data, hide_utf8_warnings)
					subfields.append(code)
					subfields.append(data)
				if to_unicode:
					field = Field(tag=entry_tag, indicators=[first_indicator, second_indicator], subfields=subfields)
				else:
					field = RawField(tag=entry_tag, indicators=[first_indicator, second_indicator], subfields=subfields)
			self.add_field(field)
			field_count += 1

		if field_count == 0:
			raise NoFieldsFound

		return self
