import json
import time


json_file_address = 'data\\database.json'


class Transaction:
    SIMBS = {
        'income': '+',
        'expence': '-',
        'transfer': ''
    }
    SYMB_FONT_SIZE = {
        '+': 60,
        '-': 100,
        '': 60
    }

    def __init__(self, tr_type, tr_time, value, to=None, category=None, from_acc=None):
        self.to_uid = None
        self.category_uid = None
        self.from_uid = None
        self.to = to
        self.category = category
        self.from_acc = from_acc
        self.name = 'unnamed transaction'

        self.refresh_info()

        self.tr_type = tr_type
        self.tr_time = tr_time
        self.symb = self.SIMBS[tr_type]
        self.symb_font_size = self.SYMB_FONT_SIZE[self.symb]
        self.value = round(value, 2)

    def time_for_dis(self):
        loc_t = time.localtime(self.tr_time)
        t = ''.join([str(loc_t.tm_mday), '.', str(loc_t.tm_mon), '.', str(loc_t.tm_year)])
        return t

    def refresh_info(self):
        if self.to is not None:
            self.name = f'Transfer to {self.to.name}'
            self.to_uid = self.to.uid
        elif self.from_acc is not None:
            self.name = f'Transfer from {self.from_acc.name}'
            self.from_uid = self.from_acc.uid
        elif self.category is not None:
            self.name = f'{self.category.name.title()}'
            self.category_uid = self.category.uid

    def get_tr_json(self):
        tr_json = {
            'tr_type': self.tr_type,
            'tr_time': self.tr_time,
            'value': self.value,
            'to_uid': self.to_uid,
            'from_uid': self.from_uid,
            'category_uid': self.category_uid
        }
        return tr_json


class Account:
    def __init__(self, name, money, uid, show):
        self.TRANSACTIONS = []
        self.name = name
        self.money = money
        self.id = f'{name}_id'
        self.valuta = 'GEL'
        self.tr_for_del = None
        self.uid = uid
        self.show = show

    def save_tr_for_del(self, tr_id):
        self.tr_for_del = self.TRANSACTIONS[int(tr_id)]

    def get_tr_for_del(self):
        return self.tr_for_del

    def remove_tr_for_del(self):
        self.tr_for_del = None

    def add_transaction(self, tr):
        self.TRANSACTIONS.append(tr)

    def refresh_transactions(self):
        for tr in self.TRANSACTIONS:
            if tr.tr_type == 'transfer':
                tr.refresh_info()

    def get_transactions(self):
        self.refresh_transactions()
        return self.TRANSACTIONS

    def del_transaction(self, tr):
        try:
            self.TRANSACTIONS.remove(tr)
        except ValueError:
            print('Transaction del error')

    def undo_transaction(self, tr: Transaction):
        self_temp = self.money
        try:
            if tr.tr_type == 'income':
                self.money = round(self.money - tr.value, 2)
                self.TRANSACTIONS.remove(tr)

            if tr.tr_type == 'expence':
                self.money = round(self.money + tr.value, 2)
                self.TRANSACTIONS.remove(tr)

        except ValueError:
            self.money = self_temp
            print('Transaction undo error')

    def undo_transfer(self, tr: Transaction):
        self_temp = self.money
        try:
            if tr.to is not None:
                self.money = round(self.money + tr.value, 2)
            if tr.from_acc is not None:
                self.money = round(self.money - tr.value, 2)
            self.TRANSACTIONS.remove(tr)
        except ValueError:
            self.money = self_temp
            print('Transfer undo error')

    @staticmethod
    def tr_time_for_dis(tr):
        return tr.time_for_dis()

    def get_account_json(self):
        account_json = {
            'uid': self.uid,
            'name': self.name,
            'money': self.money,
            'show': self.show,
            'transactions': []
        }
        for tr in self.TRANSACTIONS:
            account_json['transactions'].append(tr.get_tr_json())
        return account_json


class Category:
    def __init__(self, name, uid, show):
        self.name = name.title()
        self.uid = uid
        self.show = show

    def get_category_json(self):
        category_json = {
            'category_uid': self.uid,
            'name': self.name,
            'show': self.show
        }
        return category_json

    def update_name(self, new_name):
        self.name = new_name.title()


class Database:
    def __init__(self):
        try:
            with open(json_file_address, 'r'):
                pass
        except FileNotFoundError:
            with open(json_file_address, 'w') as f:
                f.write(json.dumps({"accounts": {},
                                    "categories": {},
                                    "account_uids": [],
                                    "category_uids": []}, indent=4))

        self.json = {}
        self.CATEGORIES = {}
        self.ACCOUNTS = {}
        self.account_uids = []
        self.category_uids = []

        self.read_data_from_json()
        self.current_acc = Account('', 0, '0', True)
        self.current_category = Category('', '0', True)
        if temp := [acc for acc in self.ACCOUNTS.values() if acc.show]:
            self.current_acc = temp[0]
        if temp := [category for category in self.CATEGORIES.values() if category.show]:
            self.current_category = temp[0]

    def read_data_from_json(self):
        try:
            with open(json_file_address, 'r') as f:
                print('start read')
                self.json = json.loads(f.read())
                print('end read')
        except json.decoder.JSONDecodeError:
            print('Data read error')
            return

        self.account_uids = self.json.get('account_uids', [])
        self.category_uids = self.json.get('category_uids', [])

        for uid in self.category_uids:
            name = self.json['categories'][uid]['name']
            show = self.json['categories'][uid]['show']
            self.CATEGORIES[uid] = Category(name, uid, show)
        for uid in self.account_uids:
            name = self.json['accounts'][uid]['name']
            money = self.json['accounts'][uid]['money']
            show = self.json['accounts'][uid]['show']
            self.ACCOUNTS[uid] = Account(name, money, uid, show)
        for uid in self.account_uids:
            for transaction in self.json['accounts'][uid]["transactions"]:
                to = None
                category = None
                from_acc = None
                tr_type = transaction['tr_type']
                tr_time = transaction['tr_time']
                value = transaction['value']

                if transaction['to_uid'] is not None:
                    to = self.ACCOUNTS[transaction['to_uid']]
                if transaction['category_uid'] is not None:
                    category = self.CATEGORIES[transaction['category_uid']]
                if transaction['from_uid'] is not None:
                    from_acc = self.ACCOUNTS[transaction['from_uid']]

                tr = Transaction(tr_type, tr_time, value, to, category, from_acc)
                self.ACCOUNTS[uid].add_transaction(tr)

    def write_data_to_json(self):
        dict_for_json = {
            'accounts': {},
            'categories': {},
            'account_uids': [],
            'category_uids': []
        }

        for uid in self.category_uids:
            dict_for_json['categories'][uid] = self.CATEGORIES[uid].get_category_json()

        for uid in self.account_uids:
            dict_for_json['accounts'][uid] = self.ACCOUNTS[uid].get_account_json()

        dict_for_json['account_uids'] = self.account_uids
        dict_for_json['category_uids'] = self.category_uids

        with open(json_file_address, 'w') as f:
            print('start save')
            f.write(json.dumps(dict_for_json, indent=4))
            print('end save')

    def generate_uid_for_new_account(self):
        account_uids_int = [0]
        for uid in self.account_uids:
            try:
                account_uids_int.append(int(uid))
            except ValueError:
                pass
        return str(max(account_uids_int) + 1)

    def generate_uid_for_new_category(self):
        category_uids_int = [0]
        for uid in self.category_uids:
            try:
                category_uids_int.append(int(uid))
            except ValueError:
                pass
        return str(max(category_uids_int) + 1)

    # ACCOUNTS
    def get_acc_by_id(self, acc_id):
        for acc in self.ACCOUNTS.values():
            if acc.id == acc_id:
                return acc
        return None

    def get_acc_by_name(self, acc_name):
        for acc in self.ACCOUNTS.values():
            if acc.name == acc_name:
                return acc
        return None

    def set_current_acc(self, acc):
        self.current_acc = acc

    def get_current_acc(self):
        return self.current_acc

    def get_ACCOUNTS_values(self):
        return [acc for acc in self.ACCOUNTS.values() if acc.show]

    def get_account_names(self):
        return [acc.name for acc in self.ACCOUNTS.values() if acc.show]

    def get_account_moneys(self):
        return [acc.money for acc in self.ACCOUNTS.values() if acc.show]

    def get_account_ids(self):
        return [acc.id for acc in self.ACCOUNTS.values() if acc.show]

    def add_account(self, name, money):
        uid = self.generate_uid_for_new_account()
        name += f'_{uid}'

        self.account_uids.append(uid)
        self.ACCOUNTS[uid] = Account(str(name), money, uid, True)
        return True

    @staticmethod
    def change_acc_name(acc, name):
        try:
            acc.name = name
            acc.id = f'{name}_id'
        except NameError:
            print('change acc name is unavailable')

    @staticmethod
    def change_acc_money(acc, money):
        try:
            acc.money = round(money, 2)
        except NameError:
            print('change acc money is unavailable')

    @staticmethod
    def del_acc(acc):
        acc.show = False
        return True

    # CATEGORIES
    def get_category_names(self):
        return [category.name for category in self.CATEGORIES.values() if category.show]

    def get_categories(self):
        return [category for category in self.CATEGORIES.values() if category.show]

    def get_category_by_name(self, category_name):
        for category in self.CATEGORIES.values():
            if category.name == category_name:
                return category
        return None

    def set_current_category(self, category):
        self.current_category = category

    def get_current_category(self):
        return self.current_category

    def add_category(self, category):
        self.CATEGORIES[category.uid] = category

    def create_category(self, name):
        uid = self.generate_uid_for_new_category()
        name += f'_{uid}'

        self.category_uids.append(uid)
        category = Category(name.title(), uid, True)
        self.add_category(category)
        return category

    @staticmethod
    def update_category_name(category, new_name):
        category.update_name(new_name)

    @staticmethod
    def del_category(category):
        category.show = False
        return True

    # TRANSACTIONS
    @staticmethod
    def get_transactions(acc):
        return acc.get_transactions()

    def make_transaction(self, tr_type, *args, **kwargs):
        if tr_type == 'income':
            self._make_transaction(tr_type, *args, **kwargs)
        elif tr_type == 'expence':
            self._make_transaction(tr_type, *args, **kwargs)
        elif tr_type == 'transfer':
            self._make_transfer(tr_type, *args, **kwargs)

    @staticmethod
    def _make_transaction(tr_type, sp1_acc: Account, value, category):
        temp = sp1_acc.money
        try:
            if tr_type == 'income':
                sp1_acc.money = round(sp1_acc.money + value, 2)
                tr = Transaction(tr_type, time.time(), value, to=None, category=category, from_acc=None)
                sp1_acc.add_transaction(tr)

            if tr_type == 'expence':
                sp1_acc.money = round(sp1_acc.money - value, 2)
                tr = Transaction(tr_type, time.time(), value, to=None, category=category, from_acc=None)
                sp1_acc.add_transaction(tr)
        except NameError:
            sp1_acc.money = temp
            print('Transaction Error')

    @staticmethod
    def _make_transfer(tr_type, from_acc: Account, value, to: Account):
        from_money = from_acc.money
        to_money = to.money
        try:
            from_acc.money = round(from_acc.money - value, 2)
            to.money = round(to.money + value, 2)
            from_tr = Transaction(tr_type, time.time(), value, to=to, category=None, from_acc=None)
            from_acc.add_transaction(from_tr)
            to_tr = Transaction(tr_type, time.time(), value, to=None, category=None, from_acc=from_acc)
            to.add_transaction(to_tr)

        except NameError:
            to.money = to_money
            from_acc.money = from_money
            print('Transaction Error')

    def del_transaction(self):
        acc = self.get_current_acc()
        tr = acc.get_tr_for_del()
        acc.del_transaction(tr)
        acc.remove_tr_for_del()

    def undo_transaction(self):
        acc = self.get_current_acc()
        tr = acc.get_tr_for_del()

        if tr.tr_type in ['income', 'expence']:
            acc.undo_transaction(tr)

        if tr.tr_type == 'transfer':
            sec_acc = None
            if tr.from_acc is not None:
                sec_acc = self.ACCOUNTS[tr.from_uid]
            elif tr.to is not None:
                sec_acc = self.ACCOUNTS[tr.to_uid]
            tr_1 = {
                'value': tr.value,
                'tr_type': tr.tr_type,
                'tr_time': tr.tr_time,
            }
            sec_tr = None

            for tr2 in sec_acc.get_transactions():
                tr_2 = {
                    'value': tr2.value,
                    'tr_type': tr2.tr_type,
                    'tr_time': tr2.tr_time,
                }
                if tr_1 == tr_2:
                    sec_tr = tr2
                    break
            if sec_tr is not None:
                acc.undo_transfer(tr)
                sec_acc.undo_transfer(sec_tr)

        acc.remove_tr_for_del()


if __name__ == '__main__':
    json_file_address = 'data/saved_info_json.json'

    def test_1(d: Database):
        print(d.ACCOUNTS['1'].TRANSACTIONS)
        print(d.ACCOUNTS['1'].money)
        d.make_transaction(d.ACCOUNTS['1'], 'income', 0.9, to=None)
        print(d.ACCOUNTS['1'].TRANSACTIONS)
        print(d.ACCOUNTS['1'].money)
        d.ACCOUNTS['1'].undo_transaction(d.get_transactions(d.ACCOUNTS['1'])[-1])
        print(d.ACCOUNTS['1'].TRANSACTIONS)
        print(d.ACCOUNTS['1'].money)
        del d
        d = Database()
        print(d.ACCOUNTS)
        print(d.ACCOUNTS['1'].money)
        print(d.ACCOUNTS['1'].TRANSACTIONS)
        print()

    def test_2(d: Database):
        print(d.ACCOUNTS)

    def test_3(d: Database):
        d.generate_uid_for_new_category()

    data = Database()
    test_3(data)
