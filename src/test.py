import sql
import excel
import web

# selected_ids = excel.get_selected_ids()
selected_ids = [1179371, 1179372]
odds = web.re_get_match_odds(selected_ids)
sql.save_odds(odds)
# print(web.re_get_match_odds(selected_ids, end = False))
