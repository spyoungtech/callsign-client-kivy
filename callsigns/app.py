import string
import webbrowser
from functools import partial
from typing import Any

import requests
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

        # TODO: use kivy.network.urlrequest.UrlRequest instead
        resp = requests.get(
            f'https://data.fcc.gov/api/license-view/basicSearch/getLicenses?searchValue={call_sign}&format=json'
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            self._fcc_lookup_failure_dialog(call_sign, origin_dialog=inst)
        data = resp.json()
        if 'Errors' in data:
            self._fcc_lookup_failure_dialog(call_sign, origin_dialog=inst)
        else:
            # TODO: implement push onto history and inline display
            # for now, we'll just show some of the info in a dialog box
            self._fcc_link_dialog(data, origin_dialog=inst)

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
        r = requests.get(f'https://callsigns.spyoung.com/callsigns/{t}.json')
        if r.status_code != 200:
            self._callsign_not_found_dialog()
        else:
            data = r.json()
            expires = r.headers.get('expires')
            self.store.put(t, data=data, expires=expires)
            self._lookup_success(t, data)

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
