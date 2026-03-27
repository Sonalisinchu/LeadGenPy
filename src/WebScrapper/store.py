import json
import os
import csv
from Configs.google_api_config import service
from dotenv import load_dotenv
load_dotenv()

_GOOGLE_UNAVAILABLE = "[WARNING] - Google API not available. Please add credentials.json to use this feature."


class Store:
    __SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    sheet = service["sheet"] if service else None

    def generate_json(self, data):
        with open('../assets/data.json', 'w+') as json_file:
            json.dump(data, json_file)

        if not data:
            return

        import pandas as pd
        import sqlite3

        try:
            df = pd.DataFrame(data)

            # AI Heuristic Scoring Function (Web Dev & CRM Agency - Growth Targeting)
            def calculate_score(row):
                score = 0
                
                # 1. Digital Infrastructure (Biggest Opportunity)
                # If they have NO website, they are invisible online = massive target.
                has_web = str(row.get('Website', 'null')).strip().lower() != 'null'
                score += 10 if has_web else 40
                
                # 2. Traffic & Footfall (Targeting Struggling Businesses)
                # Low reviews = They need CRM & Web services to grow their productivity!
                try:
                    revs = int(str(row.get('ReviewCount', '0')).replace(',', ''))
                except:
                    revs = 0
                    
                if revs == 0 or revs <= 20:
                    eng = 'Low Traffic (Needs Help)'
                    score += 30
                elif revs <= 50:
                    eng = 'Medium Traffic (Growing)'
                    score += 20
                elif revs <= 150:
                    eng = 'High Traffic'
                    score += 10
                else:
                    eng = 'Established'
                    score += 0
                    
                # 3. Contactability (Can we sell to them?)
                has_email = str(row.get('email', 'null')).strip().lower() != 'null'
                score += 15 if has_email else 0
                
                has_phone = str(row.get('PhoneNumber', 'null')).strip().lower() != 'null'
                score += 15 if has_phone else 0
                    
                return pd.Series([score, eng])

            # Apply scoring
            df[['lead_score', 'Engagement']] = df.apply(calculate_score, axis=1)
            
            # Add other requested columns
            df['Automation Level'] = 'No automation'
            df['Social Presence'] = 'Low'
            df['Notes'] = 'Heuristic Pipeline Scoring applied.'
            
            # Classification
            def classify(s):
                if s >= 80: return 'HOT'
                elif s >= 60: return 'WARM'
                elif s >= 40: return 'COLD'
                else: return 'NOT TARGET'
                
            df['lead_category'] = df['lead_score'].apply(classify)

            # Ensure score and category are at the end
            cols = [c for c in df.columns if c not in ['lead_score', 'lead_category']]
            df = df[cols + ['lead_score', 'lead_category']]

            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            excel_filename = f"leads_with_scores_{timestamp}.xlsx"
            
            desktop_xlsx = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", excel_filename)
            desktop_db = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "crm_leads.db")

            # Save Excel
            df.to_excel(desktop_xlsx, index=False)
            print(f"\n[LOG] - ✅ Excel saved to Desktop: {excel_filename}")
            
            # Save SQLite
            conn = sqlite3.connect(desktop_db)
            df.to_sql('leads_scored', conn, if_exists='append', index=False)
            conn.close()
            print(f"[LOG] - ✅ SQLite Data appended to: crm_leads.db\n")
            
        except Exception as e:
            print(f"\n[LOG] - Scoring & Export failed: {e}\n")

    def get_all_sheet_data(self):
        if not service:
            print(_GOOGLE_UNAVAILABLE)
            return []
        store = Store()
        store.remove_sheet_duplicates()
        result = self.sheet.values().get(spreadsheetId=self.__SPREADSHEET_ID, range="Sheet1").execute()
        return result.get('values', [])

    def update_personalized_email_status(self, identifier, action):
        if not service:
            print(_GOOGLE_UNAVAILABLE)
            return
        values = service["sheet"].values().get(spreadsheetId=self.__SPREADSHEET_ID, range="sheet1").execute()
        data = values.get('values', [])
        if not data:
            print(f"[LOG] - No data found in sheet1")
            return
        for row in data:
            if row[0] == identifier:
                row[-1] = action
                update_request = {
                    'range': f"sheet1!A{data.index(row) + 1}:J{data.index(row) + 1}",
                    'values': [row]
                }
                try:
                    response = service["sheet"].values().update(
                        spreadsheetId=self.__SPREADSHEET_ID, range=update_request['range'],
                        valueInputOption="USER_ENTERED", body=update_request).execute()
                    print(f'[LOG] - UPDATE LOG SAVED:\nRESPONSE: {response}')
                except Exception as error:
                    print(f'Error updating user: {error}')
                break
        else:
            print(f"[LOG] - User '{identifier}' not found in sheet1")

    def insert_one(self, values):
        if not service:
            print(_GOOGLE_UNAVAILABLE)
            return
        self.sheet.values().append(
            spreadsheetId=self.__SPREADSHEET_ID, range="Sheet1!A2:I2",
            valueInputOption="USER_ENTERED", body={'values': values}).execute()

    def get_all_dataset(self):
        with open("../assets/data.json", 'r') as json_file:
            data = json.loads(json_file.read())
            print(json.dumps(data, indent=4))

    def append_all_data_to_sheet(self):
        if not service:
            print(_GOOGLE_UNAVAILABLE)
            return
        with open("../assets/data.json", 'r') as json_file:
            data = json.loads(json_file.read())
            store = Store()
            for item in data:
                store.insert_one([list(item.values())])

    def remove_sheet_duplicates(self):
        if not service:
            print(_GOOGLE_UNAVAILABLE)
            return
        print("[LOG] - REMOVING DUPLICATE ROWS")
        request = {
            'requests': [{'deleteDuplicates': {'range': {'sheetId': 0}}}]
        }
        try:
            response = service["sheet"].batchUpdate(spreadsheetId=self.__SPREADSHEET_ID, body=request).execute()
            print(f'[LOG] - DUPLICATE ROWS REMOVED\nRESPONSE: {response}')
        except Exception as error:
            print(f'[LOG] - Error removing duplicates: {error}')