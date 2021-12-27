import itertools

from kivy.app import App
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy.uix import screenmanager
from kivy.uix.actionbar import ActionButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from database import Database

data = Database()
x = 0.24
x *= 1.46
Window.size = (1080 * x, 2240 * x)
Window.minimum_width = Window.size[0]
Window.minimum_height = Window.size[1]


class AccsMainPageLayout(GridLayout):
    def __init__(self, **kwargs):
        super(AccsMainPageLayout, self).__init__(**kwargs)
        self.cols = 1

        self.scr_layout = ScrollView()
        self.scr_layout.size_hint = (1, None)
        self.scr_layout.size = (Window.width, Window.height / 1.7)
        self.scr_layout.do_scroll_x = False
        self.scr_layout.do_scroll_y = True

        self.layout = GridLayout(cols=1)
        self.layout.cols = 1
        self.layout.size_hint = (1, None)
        self.layout.width = Window.size[0]
        self.layout.height = Window.size[1] // 3
        self.layout.padding = 10
        self.layout.bind(minimum_height=self.layout.setter('height'))

        self.accs = data.get_ACCOUNTS_values()
        self.accs_id_str = data.get_account_ids()
        self.accs_layout = GridLayout(cols=2, size_hint_y=None)

        self.add_accs_widgets()
        self.scr_layout.add_widget(self.layout)
        self.add_widget(self.scr_layout)

    def add_accs_widgets(self):
        self.accs = data.get_ACCOUNTS_values()
        self.accs_id_str = data.get_account_ids()
        self.accs_layout = GridLayout(cols=2, size_hint_y=None)

        ran = [*range(0, len(self.accs) // 2 * 2)] + ['last']
        self.layout.add_widget(self.accs_layout)
        for i, acc in zip(ran, self.accs):
            setattr(AccsMainPageLayout, acc.id, Builder.load_string(f'''
Button:
    text: '{acc.name}\\n{acc.valuta}      {str(acc.money)}'
    size_hint_y: None
    height: 70
    font_size: 15
    on_release:
        app.root.screens[0].grid.acc_pressed('{acc.id}')
'''))
            if isinstance(i, int):
                self.accs_layout.add_widget(getattr(AccsMainPageLayout, acc.id))
            else:
                self.layout.add_widget(getattr(AccsMainPageLayout, acc.id))
        try:
            self.accs_layout.size = (Window.size[0], self.accs_layout.children[0].size[1] * (len(self.accs) // 2))
        except IndexError:
            self.accs_layout.size = (Window.size[0], 0)

    def add_new_acc_pressed(self):
        if data.add_account(str('New account'), 0.0):
            self.clear_widgets()
            self.__init__()

    def acc_pressed(self, *args):
        acc = data.get_acc_by_id(args[0])
        data.set_current_acc(acc)
        r = self.parent.parent.parent.parent
        r.current = 'accDetailWindow'
        r.current_screen.manager.transition.direction = 'right'


class MainWindow(Screen):
    dropdown = DropDown()
    accs_id = GridLayout()
    grid = AccsMainPageLayout()

    def on_enter(self, *args):
        self.grid = AccsMainPageLayout()
        self.accs_id.clear_widgets()
        self.accs_id.add_widget(self.grid)

    def bt_add_new_acc_pressed(self):
        self.grid.add_new_acc_pressed()


class TransactionLayout(ScrollView):
    def __init__(self, *args, **kwargs):
        super(TransactionLayout, self).__init__(**kwargs)
        if args:
            pass
        self.pop = None
        self.size_hint = (1, None)
        self.size = (Window.width, Window.height / 1.7)
        self.do_scroll_x = False
        self.do_scroll_y = True

        self.layout = GridLayout(cols=1)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.layout.size_hint_y = None
        self.layout.row_default_height = self.layout.height * 0.8
        self.layout.height = self.layout.minimum_height
        trs = data.get_transactions(data.get_current_acc())
        self.acc = data.get_current_acc()
        self.bt_ids = []
        for count, transaction in zip(range(1, 1 + len(trs)), trs):
            bl_layout = BoxLayout()
            txt1 = ' ' + str(transaction.name) + '\n' + ' ' + str(transaction.time_for_dis())
            lbl1 = Label(text=txt1, font_size=18, size_hint_x=None, halign='left', valign='center')
            lbl1.width = 190
            lbl1.text_size = lbl1.size

            lbl_bl_layout = BoxLayout(orientation='vertical', size_hint=(1, 1), spacing=10)
            lbl_bl_layout.add_widget(lbl1)

            btn = ActionButton(size_hint_x=None, size_hint_y=None, width=80,
                               on_release=self.del_bt_pressed, icon='data\\trash.png')
            self.bt_ids.append(id(btn))

            bl_layout.add_widget(Label(text=str(count), font_size=20, size_hint_x=None, width=20))
            bl_layout.add_widget(lbl_bl_layout)
            bl_layout.add_widget(Label(text=transaction.symb, font_size=transaction.symb_font_size // 2.5,
                                       size_hint_x=None, width=20))
            bl_layout.add_widget(Label(text=f'{transaction.value}\n{self.acc.valuta}', font_size=20,
                                       size_hint_x=None, width=80))
            bl_layout.add_widget(btn)
            self.layout.add_widget(bl_layout)

        self.add_widget(self.layout)

    def del_bt_pressed(self, *args):
        i = self.bt_ids.index(id(args[0]))
        self.acc.save_tr_for_del(i)
        try:
            self.pop.open()
        except AttributeError:
            pass


class AccDetailWindow(Screen):
    transactions_grid = ScrollView()
    name_id = Label()
    money_id = Label()
    bl = BoxLayout()
    popup = Popup()
    op = Button()
    current_acc = data.get_current_acc()
    tr_layout = TransactionLayout()

    def on_enter(self, *args):
        self.popup = Builder.load_string("""
Popup:
    id: popup
    size_hint: 0.8, 0.4
    title: "Delete"
    GridLayout:
        cols: 1
        GridLayout:
            cols: 1
            Label:
                text: '      Which do you want    \\nto delete or undo transfer?'
                font_size: 18
        GridLayout:
            cols: 3
            size_hint: 1, 0.2
            Button:
                text: 'Delete'
                on_release:
                    app.root.screens[2].pop_del()
                    popup.dismiss()
            Button:
                text: 'Undo'
                on_release:
                    app.root.screens[2].pop_undo()
                    popup.dismiss()
            Button:
                text: 'Cancel'
                on_release: popup.dismiss()""")
        self.tr_layout = TransactionLayout()
        self.tr_layout.pop = self.popup
        self.current_acc = data.get_current_acc()
        self.transactions_grid.clear_widgets()
        self.transactions_grid.add_widget(self.tr_layout)
        self.name_id.text = self.get_cur_acc_name()
        self.money_id.text = f'{self.get_cur_acc_money()}  {self.current_acc.valuta}'
        self.bl.clear_widgets()

    def refresh(self):
        self.on_enter()

    def pop_open(self):
        self.popup.open()

    def pop_del(self):
        data.del_transaction()
        self.refresh()

    def pop_undo(self):
        data.undo_transaction()
        self.refresh()

    def get_current_acc(self, atr=None):
        self.current_acc = data.get_current_acc()
        try:
            temp = getattr(self.current_acc, atr)
        except AttributeError:
            temp = self.current_acc
        return temp

    def get_cur_acc_name(self):
        return self.get_current_acc('name')

    def get_cur_acc_money(self):
        return self.get_current_acc('money')


class AccEditWindow(Screen):
    txi_name = TextInput()
    txi_money = TextInput()
    current_acc = data.get_current_acc()

    def on_enter(self, *args):
        self.current_acc = data.get_current_acc()
        self.txi_name.text = self.get_acc_name()
        self.txi_money.text = str(self.get_acc_money())

    def get_acc_name(self):
        self.current_acc = data.get_current_acc()
        return self.current_acc.name

    def get_acc_money(self):
        self.current_acc = data.get_current_acc()
        return self.current_acc.money

    def bt_del_pressed(self):
        return data.del_acc(self.current_acc)

    def bt_save_pressed(self):
        data.change_acc_name(self.current_acc, self.txi_name.text)
        try:
            m = round(float(self.txi_money.text), 2)
            data.change_acc_money(self.current_acc, m)
        except ValueError:
            return False
        return True


class CategoriesLayout(ScrollView):
    def __init__(self, *args, **kwargs):
        super(CategoriesLayout, self).__init__(**kwargs)
        if args:
            pass
        self.layout = GridLayout(cols=1)
        self.add_widget(self.layout)
        self.layout.row_default_height = self.layout.height * 0.8
        self.categories = data.get_categories()
        self.edit_bt_ids = []
        self.del_bt_ids = []
        self.refresh()

    def refresh(self):
        self.layout.clear_widgets()
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.layout.size_hint_y = None
        self.layout.height = self.layout.minimum_height
        self.do_scroll_x = False
        self.do_scroll_y = True

        self.categories = data.get_categories()
        self.edit_bt_ids = []
        self.del_bt_ids = []
        for count, category in zip(range(1, 1 + len(self.categories)), self.categories):
            bl_layout = BoxLayout()
            txt1 = str(category.name)
            lbl1 = Label(text=txt1, font_size=18, size_hint_x=None, width=230, halign='left', valign='center')
            lbl1.text_size = lbl1.size

            lbl_bl_layout = BoxLayout(orientation='vertical', size_hint=(1, 1), spacing=10)
            lbl_bl_layout.add_widget(lbl1)

            edit_btn = ActionButton(size_hint_x=None, size_hint_y=None, width=80,
                                    on_release=self.edit_bt_pressed, icon='data\\edit.png')
            del_btn = ActionButton(size_hint_x=None, size_hint_y=None, width=80,
                                   on_release=self.del_bt_pressed, icon='data\\trash.png')
            self.edit_bt_ids.append(id(edit_btn))
            self.del_bt_ids.append(id(del_btn))

            bl_layout.add_widget(Label(text=str(count), font_size=20, size_hint_x=None,
                                       width=20 if len(self.categories) < 10 else 30))
            bl_layout.add_widget(lbl_bl_layout)
            bl_layout.add_widget(edit_btn)
            bl_layout.add_widget(del_btn)
            self.layout.add_widget(bl_layout)

    def del_bt_pressed(self, *args):
        category = self.categories[self.del_bt_ids.index(id(args[0]))]
        data.del_category(category)
        self.refresh()

    def edit_bt_pressed(self, *args):
        category = self.categories[self.edit_bt_ids.index(id(args[0]))]
        data.set_current_category(category)
        r = self.parent.parent.parent.parent
        r.current = 'categoryEditWindow'
        r.current_screen.manager.transition.direction = 'right'


class CategoriesWindow(Screen):
    categories_grid = ScrollView()
    cat_layout = CategoriesLayout()

    def on_enter(self, *args):
        self.cat_layout = CategoriesLayout()
        self.categories_grid.clear_widgets()
        lbl = Label(text='Categories:', font_size=25, size_hint=(None, None), width=230, halign='left', valign='center')
        lbl.text_size = lbl.size
        self.categories_grid.add_widget(lbl)
        self.categories_grid.add_widget(self.cat_layout)

    def refresh(self):
        self.on_enter()

    def add_bt_pressed(self):
        category = data.create_category('New category')
        if category:
            data.set_current_category(category)
            self.refresh()
            return True
        return False


class CategoryEditWindow(Screen):
    txi_name = TextInput()
    categoty = data.get_current_category()

    def on_enter(self, *args):
        self.categoty = data.get_current_category()
        self.txi_name.text = self.categoty.name

    def bt_save_pressed(self):
        try:
            data.update_category_name(self.categoty, self.txi_name.text)
        except AttributeError:
            return False
        return True

    def bt_del_pressed(self):
        return data.del_category(self.categoty)


class CalcWindow(Screen):
    main_lbl = ObjectProperty()

    bt_income = ObjectProperty()
    bt_expence = ObjectProperty()
    bt_transfer = ObjectProperty()

    sp1 = Spinner()
    sp2 = Spinner()
    acc_lbl_1 = ObjectProperty()
    acc_lbl_mid = ObjectProperty()
    acc_lbl_2 = ObjectProperty()

    bt_max = Button()

    current_tran = 'income'
    current_tran_lbl = ObjectProperty()
    current_tran_curse = ObjectProperty()

    categories_name = data.get_category_names()

    def bt_max_pressed(self):
        if self.sp1.text:
            self.main_lbl.text += str(data.get_acc_by_name(self.sp1.text).money)

    def bt_num_pressed(self, bt):
        last_num = self.main_lbl.text.split('+')[-1].split('-')[-1].split('*')[-1].split('/')[-1]

        if bt.text == '0':
            if last_num.count('.') == 0 and (last_num[-1:] != '0' or last_num.count('0') != len(last_num)):
                pass
            elif last_num.count('.') != 1:
                return

        if bt.text == '.':
            if last_num.count('.') != 0:
                return

        self.main_lbl.text += bt.text

    def bt_op_pressed(self, bt):
        last_2_op = self.main_lbl.text[-2:-1]
        last_op = self.main_lbl.text[-1:]

        if bt.text in ['+', '-'] and last_op in ['+', '-', '.']:
            return
        if bt.text == '*' and (last_op in ['+', '-', '/', '.'] or last_2_op == '*'):
            return
        if bt.text == '/' and (last_op in ['+', '-', '*', '.'] or last_2_op == '/'):
            return

        self.main_lbl.text += bt.text

    def bt_backspace_pressed(self):
        self.main_lbl.text = self.main_lbl.text[:-1]

    def bt_eq_pressed(self):
        try:
            def zero(n):
                if n == '0':
                    return True
                return False

            txt = self.main_lbl.text
            a = ''.join(itertools.dropwhile(zero, txt))

            exec(f'self.main_lbl.text = str(round({a}, 2))')
        except SyntaxError:
            pass

    def bt_dot_pressed(self):
        if self.main_lbl.text.split('+')[-1].split('-')[-1].split('*')[-1].split('/')[-1].count('.') == 0:
            self.main_lbl.text += self.bt_dot.text

    def bt_colors(self):
        if self.current_tran == 'income':
            self.bt_income.background_color = (0.5, 0.8, 0.8, 1)
            self.bt_expence.background_color = (1, 1, 1, 1)
            self.bt_transfer.background_color = (1, 1, 1, 1)
        elif self.current_tran == 'expence':
            self.bt_income.background_color = (1, 1, 1, 1)
            self.bt_expence.background_color = (0.5, 0.8, 0.8, 1)
            self.bt_transfer.background_color = (1, 1, 1, 1)
        elif self.current_tran == 'transfer':
            self.bt_income.background_color = (1, 1, 1, 1)
            self.bt_expence.background_color = (1, 1, 1, 1)
            self.bt_transfer.background_color = (0.5, 0.8, 0.8, 1)

    def lbl_texts(self):
        if self.current_tran == 'income':

            self.current_tran_lbl.text = '+'
            self.current_tran_lbl.font_size = 60
            self.current_tran_curse.text = 'GEL'
            self.acc_lbl_1.text = 'Account'
            self.acc_lbl_mid.text = ''
            self.acc_lbl_2.text = 'Category'

        elif self.current_tran == 'expence':

            self.current_tran_lbl.text = '-'
            self.current_tran_lbl.font_size = 100
            self.current_tran_curse.text = 'GEL'
            self.acc_lbl_1.text = 'Account'
            self.acc_lbl_mid.text = ''
            self.acc_lbl_2.text = 'Category'

        elif self.current_tran == 'transfer':

            self.current_tran_lbl.text = ''
            self.current_tran_lbl.font_size = 60
            self.current_tran_curse.text = 'GEL'
            self.acc_lbl_1.text = 'From account'
            self.acc_lbl_mid.text = '-->'
            self.acc_lbl_2.text = 'To account'

    def spinner_refresh(self):
        sp1_val = data.get_account_names()
        sp2_val = sp1_val.copy()
        categories = data.get_category_names()

        if not (self.sp1.text in sp1_val):
            if sp1_val:
                self.sp1.text = sp1_val[0]
            else:
                self.sp1.text = ''

        try:
            sp2_val.remove(self.sp1.text)
        except ValueError:
            pass
        self.sp1.values = sp1_val

        if self.current_tran == 'income':
            if not (self.sp2.text in categories):
                if categories:
                    self.sp2.text = categories[0]
                else:
                    self.sp2.text = ''
            self.sp2.values = categories

        elif self.current_tran == 'expence':

            if not (self.sp2.text in categories):
                if categories:
                    self.sp2.text = categories[-1]
                else:
                    self.sp2.text = ''
            self.sp2.values = categories

        elif self.current_tran == 'transfer':
            if sp2_val:
                self.sp2.text = sp2_val[0]
            else:
                self.sp2.text = ''
            self.sp2.values = sp2_val

    def refresh(self):
        self.lbl_texts()
        self.bt_colors()
        self.spinner_refresh()

    def ief_bt_pressed(self, bt):
        self.current_tran = bt.text.lower()
        self.refresh()

    def bt_back_pressed(self):
        self.main_lbl.text = ''

    def bt_save_pressed(self):
        temp = {
            'current_tran': self.current_tran,
            'sp1': self.sp1.text,
            'sp2': self.sp2.text,
            'lbl': self.main_lbl.text,
        }
        if all([i for i in temp.values()]):
            sp1 = data.get_acc_by_name(temp['sp1'])
            ty_type = temp['current_tran']
            try:
                val = float(temp['lbl'])
            except ValueError:
                return False
            if val != 0.0:
                if ty_type == 'transfer':
                    sp2 = data.get_acc_by_name(temp['sp2'])
                    data.make_transaction(ty_type, sp1, val, sp2)
                else:
                    sp2 = data.get_category_by_name(temp['sp2'])
                    data.make_transaction(ty_type, sp1, val, sp2)
                self.main_lbl.text = ''
                return True
        return False

    def on_enter(self, *args):
        self.refresh()


class WindowManager(ScreenManager):
    pass


kv = Builder.load_file('mywallet.kv')

tr = [
    screenmanager.NoTransition(),
    screenmanager.SlideTransition(),
    screenmanager.CardTransition(),
    screenmanager.SwapTransition(),
    screenmanager.FadeTransition(),
    screenmanager.WipeTransition(),
    screenmanager.FallOutTransition(),
    screenmanager.RiseInTransition(),
]

sm = WindowManager(transition=tr[1])

screens = [
    MainWindow(name='mainWindow'),
    CalcWindow(name='calcWindow'),
    AccDetailWindow(name='accDetailWindow'),
    AccEditWindow(name='accEditWindow'),
    CategoriesWindow(name='categoriesWindow'),
    CategoryEditWindow(name='categoryEditWindow'),
]

for screen in screens:
    sm.add_widget(screen)

sm.current = 'accEditWindow'
sm.current = 'calcWindow'
sm.current = 'accDetailWindow'
sm.current = 'categoryEditWindow'
sm.current = 'categoriesWindow'
sm.current = 'mainWindow'


class MyWalletApp(App):
    def build(self):
        self.title = 'My MyWallet'
        self.icon = 'data\\wallet.png'
        return sm

    def on_stop(self):
        # noinspection PyBroadException
        try:
            data.write_data_to_json()
        except:
            pass

    def on_pause(self):
        # noinspection PyBroadException
        try:
            data.write_data_to_json()
        except:
            pass


if __name__ == '__main__':
    MyWalletApp().run()
