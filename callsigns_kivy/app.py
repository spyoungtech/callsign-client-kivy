import json
import pathlib
import re
import string
import typing
import webbrowser
from functools import partial
from typing import Any
from typing import Self

import kivymd.icon_definitions  # noqa
from kivy.config import Config
from kivy.network.urlrequest import UrlRequest
from kivy.storage.jsonstore import JsonStore
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivymd.uix.list import OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

this_file = pathlib.Path(__file__)
icon_file = str(this_file.parent / 'callsigns-logo.png')


Config.window_icon = icon_file


# TODO: support additional alphabets
PHONETIC_WORDS = {
    'A': 'Alpha',
    'B': 'Bravo',
    'C': 'Charlie',
    'D': 'Delta',
    'E': 'Echo',
    'F': 'Foxtrot',
    'G': 'Golf',
    'H': 'Hotel',
    'I': 'India',
    'J': 'Juliet',
    'K': 'Kilo',
    'L': 'Lima',
    'M': 'Mike',
    'N': 'November',
    'O': 'Oscar',
    'P': 'Papa',
    'Q': 'Quebec',
    'R': 'Romeo',
    'S': 'Sierra',
    'T': 'Tango',
    'U': 'Uniform',
    'V': 'Victor',
    'W': 'Whiskey',
    'X': 'Xray',
    'Y': 'Yankee',
    'Z': 'Zulu',
    '0': 'Zero',
    '1': 'One',
    '2': 'Two',
    '3': 'Three',
    '4': 'Four',
    '5': 'Five',
    '6': 'Six',
    '7': 'Seven',
    '8': 'Eight',
    '9': 'Niner',
}

SYLLABLE_LENGTHS = {
    'A': 2,
    'B': 2,
    'C': 2,
    'D': 2,
    'E': 2,
    'F': 2,
    'G': 1,
    'H': 2,
    'I': 3,
    'J': 3,
    'K': 2,
    'L': 2,
    'M': 1,
    'N': 3,
    'O': 2,
    'P': 2,
    'Q': 2,
    'R': 3,
    'S': 3,
    'T': 2,
    'U': 3,
    'V': 2,
    'W': 2,
    'X': 2,
    'Y': 2,
    'Z': 2,
    '0': 2,
    '1': 1,
    '2': 1,
    '3': 1,
    '4': 1,
    '5': 1,
    '6': 1,
    '7': 2,
    '8': 1,
    '9': 2,  # 'Niner' is 2 but 'nine' (one syllable) could also be used
}

MORSE_TABLE = {
    'A': '.-',
    'B': '-...',
    'C': '-.-.',
    'D': '-..',
    'E': '.',
    'F': '..-.',
    'G': '--.',
    'H': '....',
    'I': '..',
    'J': '.---',
    'K': '-.-',
    'L': '.-..',
    'M': '--',
    'N': '-.',
    'O': '---',
    'P': '.--.',
    'Q': '--.-',
    'R': '.-.',
    'S': '...',
    'T': '-',
    'U': '..-',
    'V': '...-',
    'W': '.--',
    'X': '-..-',
    'Y': '-.--',
    'Z': '--..',
    '0': '-----',
    '1': '.----',
    '2': '..---',
    '3': '...--',
    '4': '....-',
    '5': '.....',
    '6': '-....',
    '7': '--...',
    '8': '---..',
    '9': '----.',
}


# REF: https://www.fcc.gov/sites/default/files/public_access_database_definitions_v9_0.pdf

# Amateur fields
FCC_AM_FIELD_NAMES = [
    'Record Type [AM]',
    'Unique System Identifier',
    'ULS File Number',
    'EBF Number',
    'Call Sign',
    'Operator Class',
    'Group Code',
    'Region Code',
    'Trustee Call Sign',
    'Trustee Indicator',
    'Physician Certification',
    'VE Signature',
    'Systematic Call Sign Change',
    'Vanity Call Sign Change',
    'Vanity Relationship',
    'Previous Call Sign',
    'Previous Operator Class',
    'Trustee Name',
]

# License Header fields
FCC_HD_FIELD_NAMES = [
    'Record Type',
    'Unique System Identifier',
    'ULS File Number',
    'EBF Number',
    'Call Sign',
    'License Status',
    'Radio Service Code',
    'Grant Date',
    'Expired Date',
    'Cancellation Date',
    'Eligibility Rule Num',
    'Reserved',
    'Alien',
    'Alien Government',
    'Alien Corporation',
    'Alien Officer',
    'Alien Control',
    'Revoked',
    'Convicted',
    'Adjudged',
    'Reserved',
    'Common Carrier',
    'Non Common Carrier',
    'Private Comm',
    'Fixed',
    'Mobile',
    'Radiolocation',
    'Satellite',
    'Developmental or STA or Demonstration',
    'Interconnected Service',
    'Certifier First Name',
    'Certifier MI',
    'Certifier Last Name',
    'Certifier Suffix',
    'Certifier Title',
    'Female',
    'Black or African-American',
    'Native American',
    'Hawaiian',
    'Asian',
    'White',
    'Hispanic',
    'Effective Date',
    'Last Action Date',
    'Data File Format',
    'of 89 HD',
    'Auction ID integer',
    'Broadcast Services - Regulatory Status',
    'Band Manager - Regulatory Status',
    'Broadcast Services - Type of Radio Service',
    'Alien Ruling',
    'Licensee Name Change',
    'Whitespace Indicator',
    'Operation/Performance Requirement Choice',
    'Operation/Performance Requirement Answer',
    'Discontinuation of Service',
    'Regulatory Compliance',
    '900 MHz Eligibility Certification',
    '900 MHz Transition Plan Certification',
    '900 MHz Return Spectrum Certification',
    '900 MHz Payment Certification',
]

# Entity fields
FCC_EN_FIELD_NAMES = [
    'Record Type [EN]',
    'Unique System Identifier',
    'ULS File Number',
    'EBF Number',
    'Call Sign',
    'Entity Type',
    'Licensee ID',
    'Entity Name',
    'First Name',
    'MI',
    'Last Name',
    'Suffix',
    'Phone',
    'Fax',
    'Email',
    'Street Address',
    'City',
    'State',
    'Zip Code',
    'PO Box',
    'Attention Line',
    'SGIN',
    'FCC Registration Number (FRN)',
    'Applicant Type Code',
    'Applicant Type Code Other',
    'Status Code',
    'Status Date',
    '3.7 GHz License Type',
    'Linked Unique System Identifier',
    'Linked Call Sign',
]

# REF: https://www.fcc.gov/wireless/data/public-access-files-database-downloads
#      File: ULS Code Definitions, currently https://www.fcc.gov/sites/default/files/uls_code_definitions_20240215.txt

LICENSE_STATUS_CODES = {
    'A': 'Active',
    'C': 'Canceled',
    'E': 'Expired',
    'L': 'Pending Legal Status',
    'P': 'Parent Station Canceled',
    'T': 'Terminated',
    'X': 'Term Pending',
}

OPERATOR_CLASS_CODES = {
    'A': 'Advanced',
    'E': 'Amateur Extra',
    'G': 'General',
    'N': 'Novice',
    'P': 'Technician Plus',
    'T': 'Technician',
}

UNAVAILABLE_PATTERNS = [
    # REF: "Call Sign Choices Not Available" http://www.arrl.org/vanity-call-signs
    # 1.KA2AA-KA9ZZ, KC4AAA-KC4AAF, KC4USA-KC4USZ, KG4AA-KG4ZZ, KC6AA-KC6ZZ, KL9KAA- KL9KHZ, KX6AA-KX6ZZ;
    r'^KA[2-9][A-Z][A-Z]$',
    r'^KC4AA[A-F]$',
    r'^KC4US[A-Z]$',
    r'^KG4[A-Z][A-Z]$',
    r'^KC6[A-Z][A-Z]$',
    r'^KL9K[A-H][A-Z]$',
    r'^KX6[A-Z][A-Z]$',
    # 2. Any call sign having the letters SOS or QRA-QUZ as the suffix;
    r'[A-Z]{1,2}\d(?>SOS|Q[R-U][A-Z])$',
    # 3. Any call sign having the letters AM-AZ as the prefix
    r'^A[M-Z]\d[A-Z]+$',
    # 4. Any 2-by-3 format call sign having the letter X as the first letter of the suffix;
    r'^[A-Z]{2}\dX[A-Z]{2}$',
    # 5. Any 2-by-3 format call sign having the letters AF, KF, NF, or WF as the prefix and the letters EMA as the suffix
    r'^[AKNW]F\dEMA$',
    # 6. Any 2-by-3 format call sign having the letters AA-AL as the prefix
    r'^A[A-L]\d[A-Z]{3}$',
    # 7. Any 2-by-3 format call sign having the letters NA-NZ as the prefix;
    r'^N[A-Z]\d[A-Z]{3}$',
    # 8. Any 2-by-3 format call sign having the letters WC, WK, WM, WR, or WT as the prefix (Group X call signs);
    r'^W[CKMRT]\d[A-Z]{3}$',
    # 9.  Any 2-by-3 format call sign having the letters KP, NP or WP as the prefix and the numeral 0, 6, 7, 8 or 9;
    # 10. Any 2-by-2 format call sign having the letters KP, NP or WP as the prefix and the numeral 0, 6, 7, 8 or 9;
    # 11. Any 2-by-1 format call sign having the letters KP, NP or WP as the prefix and the numeral 0, 6, 7, 8 or 9;
    r'^[KNW]P[06789][A-Z]{1,3}$',
    # 12. Call signs having the single letter prefix (K, N or W), a single digit numeral 0-9 and a single letter suffix
    r'^[KNW]\d[A-Z]$',
]


class LicenseRecord(typing.NamedTuple):
    call_sign: str
    status: str
    frn: str | None
    system_identifier: str
    first_name: str | None
    middle_initial: str | None
    last_name: str | None
    street_address: str | None
    attn_line: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    po_box: str | None
    grant_date: str | None
    expired_date: str | None
    cancellation_date: str | None
    operator_class: str | None
    group_code: str | None
    trustee_call_sign: str | None
    trustee_name: str | None
    previous_call_sign: str | None
    region_code: str | None
    vanity: str | None
    systematic: str | None

    @property
    def call_sign_morse(self) -> str:
        return ' '.join(MORSE_TABLE[c] for c in self.call_sign)

    @property
    def morse_dits(self) -> int:
        return self.call_sign_morse.count('.')

    @property
    def morse_dahs(self) -> int:
        return self.call_sign_morse.count('-')

    @property
    def format(self) -> str:
        pattern = r'([A-Z]+)\d([A-Z]+)'
        match = re.match(pattern, self.call_sign)
        if not match:
            return ''
        prefix, suffix = match.groups()
        return f'{len(prefix)}x{len(suffix)}'

    @property
    def phonetic(self) -> str:
        return ' '.join(PHONETIC_WORDS[c] for c in self.call_sign)

    @property
    def syllable_length(self) -> int:
        return self.get_syllable_length()

    def get_syllable_length(self, lengths: dict[str, int] | None = None) -> int:
        if lengths is None:
            lengths = SYLLABLE_LENGTHS
        return sum(lengths[c] for c in self.call_sign)

    @property
    def fcc_uls_link(self) -> str:
        return f'https://wireless2.fcc.gov/UlsApp/UlsSearch/license.jsp?licKey={self.system_identifier}'

    @property
    def qrz_call_sign_link(self) -> str:
        return f'https://www.qrz.com/db/{self.call_sign}'

    def as_dict(self, include_synthetic: bool = False) -> dict[str, str | int | None]:
        d: dict[str, str | int | None] = {
            'call_sign': self.call_sign,
            'status': self.status,
            'frn': self.frn,
            'system_identifier': self.system_identifier,
            'first_name': self.first_name,
            'middle_initial': self.middle_initial,
            'last_name': self.last_name,
            'street_address': self.street_address,
            'attn_line': self.attn_line,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'po_box': self.po_box,
            'grant_date': self.grant_date,
            'expired_date': self.expired_date,
            'cancellation_date': self.cancellation_date,
            'operator_class': self.operator_class,
            'group_code': self.group_code,
            'trustee_call_sign': self.trustee_call_sign,
            'trustee_name': self.trustee_name,
            'previous_call_sign': self.previous_call_sign,
            'region_code': self.region_code,
            'vanity': self.vanity,
            'systematic': self.systematic,
        }
        if include_synthetic:
            d.update(
                {
                    'call_sign_morse': self.call_sign_morse,
                    'morse_dits': self.morse_dits,
                    'morse_dahs': self.morse_dahs,
                    'format': self.format,
                    'phonetic': self.phonetic,
                    'syllable_length': self.syllable_length,
                    'fcc_uls_link': self.fcc_uls_link,
                    'qrz_call_sign_link': self.qrz_call_sign_link,
                }
            )
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            call_sign=d.get('call_sign'),  # type: ignore[arg-type]
            status=d.get('status'),  # type: ignore[arg-type]
            frn=d.get('frn'),
            system_identifier=d.get('system_identifier'),  # type: ignore[arg-type]
            first_name=d.get('first_name'),
            middle_initial=d.get('middle_initial'),
            last_name=d.get('last_name'),
            street_address=d.get('street_address'),
            attn_line=d.get('attn_line'),
            city=d.get('city'),
            state=d.get('state'),
            zip_code=d.get('zip_code'),
            po_box=d.get('po_box'),
            grant_date=d.get('grant_date'),
            expired_date=d.get('expired_date'),
            cancellation_date=d.get('cancellation_date'),
            operator_class=d.get('operator_class'),
            group_code=d.get('group_code'),
            trustee_call_sign=d.get('trustee_call_sign'),
            trustee_name=d.get('trustee_name'),
            previous_call_sign=d.get('previous_call_sign'),
            region_code=d.get('region_code'),
            vanity=d.get('vanity'),
            systematic=d.get('systematic'),
        )


class CallsignInput(MDTextField):
    def insert_text(self, substring, from_undo=False):
        for c in substring:
            if c not in string.ascii_letters + string.digits:
                return
        super().insert_text(substring.upper(), from_undo=from_undo)


class Callsigns(MDApp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def build(self):
        self.icon = icon_file
        self.store = JsonStore('callsigns.json')
        self.theme_cls.theme_style = 'Dark'
        self.container = MDGridLayout(cols=1, padding=[20, 40, 20, 20])
        self.window = MDGridLayout(cols=1, row_default_height=40)
        self.container.add_widget(self.window)
        self.dialog = None
        self.fail_dialog = None
        self.fcc_dialog = None

        title_label = MDLabel(
            text='Callsign Lookup',
            font_style='Caption',
            halign='center',
            size_hint_y=None,
            height=40,
            text_color=self.theme_cls.primary_color,
        )

        lookup_layout = MDGridLayout(cols=2)

        lookup_layout_left = MDGridLayout(cols=1, row_default_height=80)
        lookup_layout_right = MDGridLayout(cols=1)
        lookup_layout.add_widget(lookup_layout_left)
        lookup_layout.add_widget(lookup_layout_right)
        self.history_list = MDList(id='history_list')
        self.history_container = MDScrollView(self.history_list)
        lookup_layout_right.add_widget(
            MDLabel(
                text='Lookup History',
                font_style='Caption',
                halign='center',
                size_hint_y=None,
                height=40,
                text_color=self.theme_cls.primary_color,
            )
        )

        lookup_layout_right.add_widget(self.history_container)

        self.callsign_input = CallsignInput(
            hint_text='Enter callsign', helper_text='e.g., KK7LHM', size_hint_x=None, width=100, halign='center'
        )

        btn = MDRectangleFlatButton(
            text='Lookup',
            on_release=self.btnfunc,
        )
        self.window.add_widget(title_label)
        lookup_input_layout = MDGridLayout(cols=1)
        lookup_input_layout.add_widget(self.callsign_input)
        lookup_input_layout.add_widget(btn)

        lookup_layout_left.add_widget(lookup_input_layout)
        self.info_layout = MDGridLayout(cols=1)

        lookup_layout_left.add_widget(self.info_layout)

        self.window.add_widget(lookup_layout)
        return self.container

    def _callsign_not_found_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                text='Callsign not found.\nIf this callsign was issued very recently (last day or so) use the FCC Lookup',
                buttons=[
                    MDFlatButton(
                        text='OK',
                        theme_text_color='Custom',
                        text_color=self.theme_cls.primary_color,
                        on_release=self._dismiss_dialog,
                    ),
                    MDFlatButton(
                        text='FCC LOOKUP',
                        theme_text_color='Custom',
                        text_color=self.theme_cls.primary_color,
                        on_release=self._fcc_fallback_lookup,
                    ),
                ],
            )

        self.dialog.open()

    def _fcc_lookup_failure_dialog(self, call_sign=None, origin_dialog=None):
        def _dismiss(inst):
            self._dismiss_dialog(inst)
            if origin_dialog is not None:
                self._dismiss_dialog(origin_dialog)

        self.fail_dialog = MDDialog(
            text=f'Could not locate data for call sign{(" " + call_sign + " ") if call_sign else ""}. Please try a different call',
            buttons=[
                MDFlatButton(
                    text='OK',
                    text_color=self.theme_cls.primary_color,
                    on_release=_dismiss,
                )
            ],
        )
        self.fail_dialog.open()

    @staticmethod
    def _find_dialog_parent(obj):
        while True:
            if isinstance(obj, MDDialog):
                return obj
            elif hasattr(obj, 'parent'):
                obj = obj.parent
            else:
                raise Exception('No dialog found')

    def _fcc_link_dialog(self, fccdata, origin_dialog=None):
        # example fccdata:
        # {'status': 'OK',
        #  'Licenses': {'page': '1',
        #               'rowPerPage': '100',
        #               'totalRows': '1',
        #               'lastUpdate': 'Apr 7, 2023',
        #               'License': [{'licName': 'Last, First I',
        #                            'frn': '0012345678',
        #                            'callsign': 'AA0ZZZ',
        #                            'categoryDesc': 'Personal Use',
        #                            'serviceDesc': 'Amateur',
        #                            'statusDesc': 'Active',
        #                            'expiredDate': '01/01/2033',
        #                            'licenseID': '1234567',
        #                            'licDetailURL': 'http://wireless2.fcc.gov/UlsApp/UlsSearch/license.jsp?__newWindow=false&licKey=1234567'}]}}

        def _dismiss(inst):
            self._dismiss_dialog(inst)
            if origin_dialog is not None:
                self._dismiss_dialog(origin_dialog)

        # XXX: this first result may not be the correct call sign
        # The FCC License View API can return other call signs than was given in the parameter
        # esp. when the searched call sign is a substring of another call sign
        data = fccdata['Licenses']['License'][0]

        # TODO: validate result is for the requested call sign

        self.fcc_dialog = MDDialog(
            text=f'Call sign {data["callsign"]} found!\n'
            f'Name: {data["licName"]}\n'
            f'Status: {data["statusDesc"]}\n\nSee FCC profile page for full details',
            buttons=[
                MDFlatButton(
                    text='Open FCC Profile',
                    theme_text_color='Custom',
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x: webbrowser.open(data['licDetailURL']),
                ),
                MDFlatButton(
                    text='Done',
                    theme_text_color='Custom',
                    text_color=self.theme_cls.primary_color,
                    on_release=_dismiss,
                ),
            ],
        )
        self.fcc_dialog.open()

    def _fcc_fallback_lookup(self, inst):
        call_sign = self.callsign_input.text.upper()

        def on_success(req, result):
            data = result
            if 'Errors' in data:
                self._fcc_lookup_failure_dialog(call_sign, origin_dialog=inst)
            # TODO: implement push onto history and inline display
            self._fcc_link_dialog(data, origin_dialog=inst)

        def on_failure(req, result):
            self._fcc_lookup_failure_dialog(call_sign, origin_dialog=inst)

        def on_error(req, error):
            self._fcc_lookup_failure_dialog(call_sign, origin_dialog=inst)

        def on_progress(req, current_size, total_size):
            pass  # You can add progress handling if needed

        url = f'https://data.fcc.gov/api/license-view/basicSearch/getLicenses?searchValue={call_sign}&format=json'
        UrlRequest(url, on_success=on_success, on_failure=on_failure, on_error=on_error, on_progress=on_progress)

    def _dismiss_dialog(self, inst):
        dialog = self._find_dialog_parent(inst)
        dialog.dismiss(force=True)

    def btnfunc(self, obj):
        t = self.callsign_input.text.upper()
        if not t:
            return
        if self.store.exists(t):
            data = self.store.get(t)['data']
            self._lookup_success(t, data)
            return

        def on_success(req, result):
            data = result
            if isinstance(data, bytes):
                data = json.loads(data.decode('utf-8'))
            data = [LicenseRecord.from_dict(lic_data).as_dict(include_synthetic=True) for lic_data in data]
            expires = req.resp_headers.get('expires')
            self.store.put(t, data=data, expires=expires)
            self._lookup_success(t, data)

        def on_failure(req, result):
            self._callsign_not_found_dialog()

        def on_error(req, error):
            self._callsign_not_found_dialog()

        def on_progress(req, current_size, total_size):
            pass  # You can add progress handling if needed

        url = f'https://callsigns.spyoung.com/callsigns/{t}.json'
        UrlRequest(url, on_success=on_success, on_failure=on_failure, on_error=on_error, on_progress=on_progress)

    def _push_lookup_history(self, callsign: str, data: list[dict[str, Any]]):
        if len(data) == 1:
            current = data[0]
        else:
            current = data[-1]
        name = self._format_name(current)
        self.history_list.add_widget(
            OneLineListItem(
                text=f'{callsign} ({name})',
                on_release=partial(self._show_info, data),
                text_color=self.theme_cls.primary_color,
            ),
            index=len(self.history_list.children),
        )

    def _format_name(self, record_data) -> str:
        return ' '.join(
            i for i in (record_data['first_name'], record_data['middle_initial'], record_data['last_name']) if i
        )

    def _format_addr(self, record_data: dict[str, Any]) -> str:
        name = self._format_name(record_data)
        addr_info = '\n'.join(
            i
            for i in [
                name,
                record_data['street_address'],
                record_data['attn_line'],
                f"PO Box {record_data['po_box']}" if record_data['po_box'] else '',
                ', '.join(
                    [
                        record_data['city'],
                        ' '.join(
                            (
                                record_data['state'],
                                record_data['zip_code'],
                            )
                        ),
                    ]
                ),
            ]
            if i
        )
        return addr_info

    def _lookup_success(self, callsign: str, data: list[dict[str, Any]]) -> None:
        self._push_lookup_history(callsign, data)
        self._show_info(data)

    def _show_info(self, data: list[dict[str, Any]], inst=None):
        if len(data) == 1:
            current = data[0]
        else:
            current = data[-1]
        addr_info = self._format_addr(current)

        self.info_layout.clear_widgets()

        self.info_call_sign = MDLabel()
        self.info_addr = MDLabel()
        self.info_status = MDLabel()
        self.info_frn = MDLabel()
        self.info_grant_date = MDLabel()
        self.info_expired_date = MDLabel()
        self.info_cancellation_date = MDLabel()
        self.info_operator_class = MDLabel()
        self.info_phonetic = MDLabel()
        self.info_vanity = MDLabel()

        statuses = {'A': 'Active', 'C': 'Cancelled', 'E': 'Expired', 'T': 'Terminated'}

        status = statuses.get(current['status'], current['status'])

        self.info_addr.text = addr_info
        self.info_status.text = f'Status: {status}' if status else ''
        self.info_grant_date.text = f"Grant Date: {current['grant_date']}"
        self.info_expired_date.text = f"Expiration: {current['expired_date']}"
        self.info_cancellation_date.text = f"Cancellation Date: {current['cancellation_date']}"
        self.info_phonetic.text = f"phonetic: {current['phonetic']}"
        self.info_call_sign.text = current['call_sign'] + (' (vanity)' if current['vanity'] else '')
        self.info_frn.text = f"FRN: {current['frn']}" if current['frn'] else ''
        self.info_operator_class.text = f"Operator Class: {current['operator_class']}"

        for w in [
            self.info_call_sign,
            self.info_addr,
            self.info_status,
            self.info_frn,
            self.info_grant_date,
            self.info_expired_date,
            self.info_cancellation_date,
            self.info_operator_class,
            self.info_phonetic,
        ]:
            if w.text:
                self.info_layout.add_widget(w)

    def on_start(self):
        for call_sign, info in self.store._data.items():
            data = info['data']
            self._push_lookup_history(call_sign, data)


if __name__ == '__main__':
    Callsigns().run()
