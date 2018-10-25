import os
import re
import psycopg2
import datetime

# list of variables in SWAT output files used to index columns
sub_column_list = ['', 'SUB', 'GIS', 'MO', 'DA', 'YR', 'AREAkm2', 'PRECIPmm', 'SNOMELTmm', 'PETmm', 'ETmm', 'SWmm', 'PERCmm',
              'SURQmm', 'GW_Qmm', 'WYLDmm', 'SYLDt/ha', 'ORGNkg/ha', 'ORGPkg/ha', 'NSURQkg/ha', 'SOLPkg/ha',
              'SEDPkg/ha', 'LATQmm', 'LATNO3kg/ha', 'GWNO3kg/ha', 'CHOLAmic/L', 'CBODUmg/L', 'DOXQmg/L', 'TNO3kg/ha']
rchmonth_column_list = ['', 'RCH', 'GIS', 'MON', 'AREAkm2', 'FLOW_INcms', 'FLOW_OUTcms', 'EVAPcms', 'TLOSScms', 'SED_INtons',
                  'SED_OUTtons', 'SEDCONCmg/kg', 'ORGN_INkg', 'ORGN_OUTkg', 'ORGP_INkg', 'ORGP_OUTkg', 'NO3_INkg',
                  'NO3_OUTkg', 'NH4_INkg', 'NH4_OUTkg', 'NO2_INkg', 'NO2_OUTkg', 'MINP_INkg', 'MINP_OUTkg',
                  'CHLA_INkg', 'CHLA_OUTkg', 'CBOD_INkg', 'CBOD_OUTkg', 'DISOX_INkg', 'DISOX_OUTkg', 'SOLPST_INmg',
                  'SOLPST_OUTmg', 'SORPST_INmg', 'SORPST_OUTmg', 'REACTPSTmg', 'VOLPSTmg', 'SETTLPSTmg', 'RESUSP_PSTmg',
                  'DIFFUSEPSTmg', 'REACBEDPSTmg', 'BURYPSTmg', 'BED_PSTmg', 'BACTP_OUTct', 'BACTLP_OUTct', 'CMETAL#1kg',
                  'CMETAL#2kg', 'CMETAL#3kg', 'TOTNkg', 'TOTPkg', 'NO3ConcMg/l', 'WTMPdegc']
rchday_column_list = ['', 'RCH', 'GIS', 'MO', 'DA', 'YR', 'AREAkm2', 'FLOW_INcms', 'FLOW_OUTcms', 'EVAPcms', 'TLOSScms', 'SED_INtons',
                  'SED_OUTtons', 'SEDCONCmg/kg', 'ORGN_INkg', 'ORGN_OUTkg', 'ORGP_INkg', 'ORGP_OUTkg', 'NO3_INkg',
                  'NO3_OUTkg', 'NH4_INkg', 'NH4_OUTkg', 'NO2_INkg', 'NO2_OUTkg', 'MINP_INkg', 'MINP_OUTkg',
                  'CHLA_INkg', 'CHLA_OUTkg', 'CBOD_INkg', 'CBOD_OUTkg', 'DISOX_INkg', 'DISOX_OUTkg', 'SOLPST_INmg',
                  'SOLPST_OUTmg', 'SORPST_INmg', 'SORPST_OUTmg', 'REACTPSTmg', 'VOLPSTmg', 'SETTLPSTmg', 'RESUSP_PSTmg',
                  'DIFFUSEPSTmg', 'REACBEDPSTmg', 'BURYPSTmg', 'BED_PSTmg', 'BACTP_OUTct', 'BACTLP_OUTct', 'CMETAL#1kg',
                  'CMETAL#2kg', 'CMETAL#3kg', 'TOTNkg', 'TOTPkg', 'NO3ConcMg/l', 'WTMPdegc']

# User specified options
data_path = '/home/ubuntu/swat_data/lmrb/' #path to folder containing all data for new model
watershed_name = 'lmrb' #name of watershed to be used throughout the app (needs to be different from pre-existing watershed names)
sub_vars = ['PRECIPmm', 'PETmm', 'ETmm', 'SWmm', 'PERCmm', 'SURQmm', 'GW_Qmm', 'WYLDmm', 'SYLDt/ha'] #vars from output.sub file to upload to db
rch_vars = ['FLOW_INcms', 'FLOW_OUTcms', 'EVAPcms', 'SED_INtons', 'SED_OUTtons', 'SEDCONCmg/kg', 'ORGN_INkg', 'ORGN_OUTkg', 'DISOX_INkg', 'DISOX_OUTkg'] #vars from output.rch file to upload to db


def upload_swat_outputs(output_path, watershed_name, sub_vars, rch_vars):
    conn = psycopg2.connect('dbname=swat2_swat_db user=tethys_super password=pass host=localhost port=5435')
    cur = conn.cursor()
    cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
    records = cur.fetchall()

    if len(records) > 0:
        print("watershed name already exists")
    else:
        cur.execute("""INSERT INTO watershed (name) VALUES ('{0}')""".format(watershed_name))

        conn.commit()

        cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
        records = cur.fetchall()
        print(records)
    watershed_id = records[0][0]
    print(watershed_id)

    for file in os.listdir(output_path):
        #upload output.sub data to PostgreSQL database
        if file.endswith('.sub'):
            print('sub')
            sub_path = os.path.join(output_path, file)
            f = open(sub_path)
            for skip_line in f:
                if 'AREAkm2' in skip_line:
                    break
            for num, line in enumerate(f, 1):
                line = str(line.strip())
                columns = line.split()
                if re.match('^(?=.*[0-9]$)(?=.*[a-zA-Z])', columns[0]): #split the first column if column[0] and column[1] don't have a space between them
                    split = columns[0]
                    columns[0] = split[:6]
                    columns.insert(1, split[6:])
                for idx, item in enumerate(sub_vars):
                    sub = int(columns[1])
                    dt = datetime.date(int(columns[5]), int(columns[3]), int(columns[4]))
                    var_name = item
                    val = float(columns[sub_column_list.index(item)])
                    cur.execute("""INSERT INTO output_sub (watershed_id, year_month_day, sub_id, var_name, val)
                         VALUES ({0}, '{1}', {2}, '{3}', {4})""".format(watershed_id, dt, sub, var_name, val))
                conn.commit()


        #upload output.rch data to PostgreSQL database
        if file.endswith('.rch'):
            if 'daily' in file:
                print('rch')
                rchday_path = os.path.join(output_path, file)
                f = open(rchday_path)
                for skip_line in f:
                    if 'AREAkm2' in skip_line:
                        break
                for num, line in enumerate(f, 1):
                    line = str(line.strip())
                    columns = line.split()
                    for idx, item in enumerate(rch_vars):
                        reach = int(columns[1])
                        dt = datetime.date(int(columns[5]), int(columns[3]), int(columns[4]))
                        var_name = item
                        val = float(columns[rchday_column_list.index(item)])
                        cur.execute("""INSERT INTO output_rch_day (watershed_id, year_month_day, reach_id, var_name, val)
                                    VALUES ({0}, '{1}', {2}, '{3}', {4})""".format(watershed_id, dt, reach, var_name, val))
                    conn.commit()

    sub_vars = ','.join(sub_vars)
    print(sub_vars)

    cur.execute(
        """SELECT MIN(year_month_day) FROM output_sub WHERE watershed_id={0}""".format(watershed_id)
    )
    sub_start = cur.fetchall()[0][0]
    print(sub_start)

    cur.execute(
        """SELECT MAX(year_month_day) FROM output_sub WHERE watershed_id={0}""".format(watershed_id)
    )

    sub_end = cur.fetchall()[0][0]
    print(sub_end)
    rch_vars = ','.join(rch_vars)
    print(rch_vars)

    cur.execute(
        """SELECT MIN(year_month_day) FROM output_rch_day WHERE watershed_id={0}""".format(watershed_id)
    )
    rchday_start = cur.fetchall()[0][0]
    print(rchday_start)

    cur.execute(
        """SELECT MAX(year_month_day) FROM output_rch_day WHERE watershed_id={0}""".format(watershed_id)
    )
    rchday_end = cur.fetchall()[0][0]
    print(rchday_end)

    cur.execute("""INSERT INTO watershed_info (watershed_id, rchday_start, rchday_end, rch_vars, sub_start, sub_end, sub_vars)
                VALUES ({0}, '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')""".format(watershed_id, rchday_start, rchday_end, rch_vars, sub_start, sub_end, sub_vars)
                )
    conn.commit()
    conn.close()


upload_swat_outputs(os.path.join(data_path, 'Outputs'), watershed_name, sub_vars, rch_vars)

# if file.endswith('.hru'):
#     print('hru')
#     hru_path = os.path.join(output_path, file)
#     f = open(hru_path)
#     for skip_line in f:
#         if 'LULC' in skip_line:
#             break
#
#     for num, line in enumerate(f, 1):
#         line = str(line.strip())
#         columns = line.split()
#         if len(columns[0]) > 4:
#             split = columns[0]
#             split_parts = re.split('(\d.*)', split)
#             columns[0] = split_parts[0]
#             columns.insert(1, split_parts[1])
#         if int(columns[7]) == year_one:
#             for idx, item in enumerate(hru_vars):
#                 lulc = columns[0]
#                 hru = int(columns[1])
#                 sub = int(columns[3])
#                 dt = datetime.date(int(columns[7]), int(columns[5]), int(columns[6]))
#                 var_name = item
#                 val = float(columns[hru_column_list.index(item)])
#                 cur.execute("""INSERT INTO output_hru (watershed_id, month_day_year, sub_id, hru_id, lulc, var_name, val)
#                      VALUES ({0}, '{1}', {2}, {3}, '{4}', '{5}', {6})""".format(watershed_id, dt, sub, hru, lulc,
#                                                                                 var_name, val))
#
#             conn.commit()
#         else:
#             break