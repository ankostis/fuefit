import sys; sys.path.append(r'D:\Work\fuefit.git\fuefit\excel'); import os; from xlwings import Workbook, Range; wb = Workbook(r'D:\Work\fuefit.git\fuefit\excel\fuefit_excel_runner.xlsm'); import fuefit_excel_runner as mypy; import fuefitRange('B4').value = 'fuefit-%s, %s'% (fuefit.__version__, fuefit.__updated__)vehs_df = mypy.read_input_as_df('D2')exp_pairs = mypy.build_models(vehs_df)exp_pairs = mypy.run_experiments(exp_pairs)
