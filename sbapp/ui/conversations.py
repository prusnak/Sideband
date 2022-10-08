import RNS
import time

from kivy.metrics import dp,sp
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.list import MDList, IconLeftWidget, IconRightWidget, OneLineAvatarIconListItem
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog


class NewConv(BoxLayout):
    pass


class MsgSync(BoxLayout):
    pass


class ConvSettings(BoxLayout):
    disp_name = StringProperty()
    context_dest = StringProperty()
    trusted = BooleanProperty()


class Conversations():
    def __init__(self, app):
        self.app = app
        self.context_dests = []
        self.added_item_dests = []
        self.list = None
        self.conversation_dropdown = None
        self.update()

    def reload(self):
        self.clear_list()
        self.update()

    def clear_list(self):
        if self.list != None:
            self.list.clear_widgets()

        self.context_dests = []
        self.added_item_dests = []

    def update(self):
        if self.app.sideband.getstate("app.flags.unread_conversations"):
            self.clear_list()
        
        self.context_dests = self.app.sideband.list_conversations()
        self.update_widget()

        self.app.sideband.setstate("app.flags.unread_conversations", False)
        self.app.sideband.setstate("app.flags.new_conversations", False)

    def update_widget(self):
        us = time.time()
        RNS.log("Updating conversation list widgets", RNS.LOG_DEBUG)
        if self.list == None:
            self.list = MDList()
            
        for conv in self.context_dests:
            context_dest = conv["dest"]
            unread = conv["unread"]

            if not context_dest in self.added_item_dests:
                if self.app.sideband.is_trusted(context_dest):
                    if unread:
                        trust_icon = "email-seal"
                    else:
                        trust_icon = "account-check"
                else:
                    if unread:
                        trust_icon = "email"
                    else:
                        trust_icon = "account-question"

                iconl = IconLeftWidget(icon=trust_icon, on_release=self.app.conversation_action)
                item = OneLineAvatarIconListItem(text=self.app.sideband.peer_display_name(context_dest), on_release=self.app.conversation_action)
                item.add_widget(iconl)
                item.sb_uid = context_dest
                iconl.sb_uid = context_dest

                def gen_edit(dest, item):
                    def x():
                        dest = self.conversation_dropdown.context_dest
                        try:
                            disp_name = self.app.sideband.raw_display_name(dest)
                            is_trusted = self.app.sideband.is_trusted(dest)

                            yes_button = MDRectangleFlatButton(text="Save",font_size=sp(18), theme_text_color="Custom", line_color=self.app.color_accept, text_color=self.app.color_accept)
                            no_button = MDRectangleFlatButton(text="Cancel",font_size=sp(18))
                            dialog_content = ConvSettings(disp_name=disp_name, context_dest=RNS.hexrep(dest, delimit=False), trusted=is_trusted)
                            dialog = MDDialog(
                                title="Edit Conversation",
                                text= "With "+RNS.prettyhexrep(dest),
                                type="custom",
                                content_cls=dialog_content,
                                buttons=[ yes_button, no_button ],
                                # elevation=0,
                            )
                            dialog.d_content = dialog_content
                            def dl_yes(s):
                                try:
                                    name = dialog.d_content.ids["name_field"].text
                                    trusted = dialog.d_content.ids["trusted_switch"].active
                                    if trusted:
                                        RNS.log("Setting Trusted "+str(trusted))
                                        self.app.sideband.trusted_conversation(dest)
                                    else:
                                        RNS.log("Setting Untrusted "+str(trusted))
                                        self.app.sideband.untrusted_conversation(dest)

                                    RNS.log("Name="+name)
                                    self.app.sideband.named_conversation(name, dest)

                                except Exception as e:
                                    RNS.log("Error while saving conversation settings: "+str(e), RNS.LOG_ERROR)

                                dialog.dismiss()

                                def cb(dt):
                                    self.reload()
                                Clock.schedule_once(cb, 0.2)

                            def dl_no(s):
                                dialog.dismiss()

                            yes_button.bind(on_release=dl_yes)
                            no_button.bind(on_release=dl_no)
                            item.dmenu.dismiss()
                            dialog.open()
                        except Exception as e:
                            RNS.log("Error while creating conversation settings: "+str(e), RNS.LOG_ERROR)

                    return x

                def gen_clear(dest, item):
                    def x():
                        dest = self.conversation_dropdown.context_dest
                        yes_button = MDRectangleFlatButton(text="Yes",font_size=sp(18), theme_text_color="Custom", line_color=self.app.color_reject, text_color=self.app.color_reject)
                        no_button = MDRectangleFlatButton(text="No",font_size=sp(18))

                        dialog = MDDialog(
                            title="Clear all messages in conversation?",
                            buttons=[ yes_button, no_button ],
                            # elevation=0,
                        )
                        def dl_yes(s):
                            dialog.dismiss()
                            self.app.sideband.clear_conversation(dest)
                        def dl_no(s):
                            dialog.dismiss()

                        yes_button.bind(on_release=dl_yes)
                        no_button.bind(on_release=dl_no)
                        item.dmenu.dismiss()
                        dialog.open()
                    return x

                def gen_del(dest, item):
                    def x():
                        yes_button = MDRectangleFlatButton(text="Yes",font_size=sp(18), theme_text_color="Custom", line_color=self.app.color_reject, text_color=self.app.color_reject)
                        no_button = MDRectangleFlatButton(text="No",font_size=sp(18))
                        dialog = MDDialog(
                            title="Delete conversation?",
                            buttons=[ yes_button, no_button ],
                            # elevation=0,
                        )
                        def dl_yes(s):
                            dialog.dismiss()
                            self.app.sideband.delete_conversation(self.conversation_dropdown.context_dest)
                            def cb(dt):
                                self.reload()
                            Clock.schedule_once(cb, 0.2)
                        def dl_no(s):
                            dialog.dismiss()

                        yes_button.bind(on_release=dl_yes)
                        no_button.bind(on_release=dl_no)
                        item.dmenu.dismiss()
                        dialog.open()
                    return x

                if self.conversation_dropdown == None:
                    dmi_h = 40
                    dm_items = [
                        {
                            "viewclass": "OneLineListItem",
                            "text": "Edit",
                            "height": dp(dmi_h),
                            "on_release": gen_edit(context_dest, item)
                        },
                        {
                            "text": "Clear Messages",
                            "viewclass": "OneLineListItem",
                            "height": dp(dmi_h),
                            "on_release": gen_clear(context_dest, item)
                        },
                        {
                            "text": "Delete Conversation",
                            "viewclass": "OneLineListItem",
                            "height": dp(dmi_h),
                            "on_release": gen_del(context_dest, item)
                        }
                    ]

                    self.conversation_dropdown = MDDropdownMenu(
                        caller=None,
                        items=dm_items,
                        position="auto",
                        width_mult=4,
                        elevation=1,
                        radius=dp(3),
                        opening_transition="linear",
                        opening_time=0.0,
                    )

                item.iconr = IconRightWidget(icon="dots-vertical");
                item.dmenu = self.conversation_dropdown

                def callback_factory(ref, dest):
                    def x(sender):
                        self.conversation_dropdown.context_dest = dest
                        ref.dmenu.caller = ref.iconr
                        ref.dmenu.open()
                    return x

                item.iconr.bind(on_release=callback_factory(item, context_dest))

                item.add_widget(item.iconr)
                
                self.added_item_dests.append(context_dest)
                self.list.add_widget(item)

        RNS.log("Updated conversation list widgets in "+RNS.prettytime(time.time()-us), RNS.LOG_DEBUG)

    def get_widget(self):
        return self.list