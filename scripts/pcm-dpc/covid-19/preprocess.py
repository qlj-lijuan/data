# Lint as: python3
"""
This script preprocesses the covid19 data from Italy Department of Civil
Protection for importing into Data Commons.
"""

import pandas as pd

class PcmDpc:
    """download the csv files and preprocess it for importing into
    DataCommons"""
    def preprocess(self):
        """clean and save the CSV file"""
        self.data = pd.read_csv(self.csvpath)
        assert 'note' in self.data.columns
        self.data = self.data.drop(columns=['note'])
        self._translate()
        # drop the time, keep the date only
        self.data['Date'] = self.data['Date'].str[0:10]
        self.set_location() # prepocess the geo ids
        self.data.to_csv(self.name + '.csv', index=False)

    def generate_tmcf(self):
        """generate the template mcf"""
        geo_node = self.geo_template() # write the geo node to template mcf
        TEMPLATE = ('Node: E:pcm-dpc->E{index}\n'
                    'typeOf: dcs:StatVarObservation\n'
                    'variableMeasured: dcs:{SVname}\n'
                    'observationAbout: {geoNode}\n'
                    'observationDate: C:pcm-dpc->Date\n'
                    'value: C:pcm-dpc->{SVname}\n\n')
        idx = 1
        with open(self.name + '.tmcf', 'a') as f_out:
            for statvar in self.stat_vars:
                f_out.write(TEMPLATE.format_map({'index': idx,
                    'SVname': statvar, 'geoNode': geo_node}))
                idx += 1

    def _translate(self):
        """translate coloumn names from italian to english"""
        it2en = {'data': 'Date', 'stato': 'State',
                 'codice_regione':'RegionCode',
                 'denominazione_regione': 'RegionName',
                 'codice_provincia': 'ProvinceCode',
                 'denominazione_provincia': 'ProvinceName',
                 'sigla_provincia': 'ProvinceAbbreviation',
                 'lat': 'Latitude', 'long': 'Longitude',
                 'ricoverati_con_sintomi': 'Count_MedicalConditionIncident'
                 '_COVID_19_PatientHospitalizedWithSymptoms',
                 'terapia_intensiva': 'Count_MedicalConditionIncident'
                 '_COVID_19_PatientInICU',
                 'totale_ospedalizzati': 'Count_MedicalConditionIncident'
                 '_COVID_19_PatientHospitalized',
                 'isolamento_domiciliare': 'Count_MedicalConditionIncident'
                 '_COVID_19_PatientInHomeIsolation',
                 'totale_positivi': 'Count_MedicalConditionIncident'
                 '_COVID_19_ActiveCase',
                 'variazione_totale_positivi': 'IncrementalCount_Medical'
                 'ConditionIncident_COVID_19_PositiveCase',
                 'nuovi_positivi': 'IncrementalCount_MedicalConditionIncident'
                 '_COVID_19_ActiveCase',
                 'dimessi_guariti': 'CumulativeCount_MedicalConditionIncident'
                 '_COVID_19_PatientRecovered',
                 'deceduti': 'CumulativeCount_MedicalConditionIncident_COVID_19'
                 '_PatientDeceased',
                 'totale_casi':'CumulativeCount_MedicalConditionIncident_'
                 'COVID_19_PositiveCase',
                 'tamponi': 'CumulativeCount_MedicalTest_COVID_19',
                 'casi_testati': 'CumulativeCount_Person_COVID_19_Tested',
                 'casi_da_sospetto_diagnostico': 'PositiveCasesFromClinicActivity',
                 'casi_da_screening': 'PositiveCasesFromSurveyAndTest'}
        for col in self.data.columns:
            assert col in it2en
        self.data = self.data.rename(columns=it2en)

    def set_location(self):
        raise NotImplementedError

    def geo_template(self):
        raise NotImplementedError

STAT_VARS = ['Count_MedicalConditionIncident_COVID_19_'
             'PatientHospitalizedWithSymptoms',
             'Count_MedicalConditionIncident_COVID_19_PatientInICU',
             'Count_MedicalConditionIncident_COVID_19_'
             'PatientHospitalized',
             'Count_MedicalConditionIncident_COVID_19_'
             'PatientInHomeIsolation',
             'Count_MedicalConditionIncident_COVID_19_ActiveCase',
             'IncrementalCount_MedicalConditionIncident_COVID_19_'
             'PositiveCase',
             'IncrementalCount_MedicalConditionIncident_COVID_19_'
             'ActiveCase',
             'CumulativeCount_MedicalConditionIncident_COVID_19_'
             'PatientRecovered',
             'CumulativeCount_MedicalConditionIncident_COVID_19'
             '_PatientDeceased',
             'CumulativeCount_MedicalConditionIncident_'
             'COVID_19_PositiveCase',
             'CumulativeCount_MedicalTest_COVID_19',
             'CumulativeCount_Person_COVID_19_Tested']

class PcmDpcNational(PcmDpc):
    """subclass processing national data"""
    def __init__(self):
        self.csvpath = ('https://raw.githubusercontent.com/pcm-dpc/COVID-19/'
                        'master/dati-andamento-nazionale/dpc-covid19-ita-and'
                        'amento-nazionale.csv')
        self.name = "dpc-covid19-ita-national-trend"
        self.stat_vars = STAT_VARS

    def set_location(self):
        assert (self.data['State'] == 'ITA').all()
        self.data = self.data.drop(columns=['State'])

    def geo_template(self):
        return 'dcid:country/ITA'


class PcmDpcRegions(PcmDpc):
    """subclass processing regional data"""
    def __init__(self):
        self.csvpath = ('https://raw.githubusercontent.com/pcm-dpc/COVID-19/'
                        'master/dati-regioni/dpc-covid19-ita-regioni.csv')
        self.name = "dpc-covid19-ita-regional"
        self.stat_vars = STAT_VARS

    def set_location(self):
        region_code_path = ('https://raw.githubusercontent.com/qlj-lijuan/data/'
                            'master/scripts/istat/geos/cleaned/ISTAT_region.csv')
        region_code = pd.read_csv(region_code_path)[['Region Code', 'NUTS2']]
        code_dict = region_code.set_index('Region Code').to_dict()['NUTS2']
        # region code 21 and 22 is missing from the dict above, add manually here.
        code_dict[21] = 'nuts/ITH1'
        code_dict[22] = 'nuts/ITH2'
        self.data['Location'] = self.data['RegionCode'].map(code_dict)
        self.data = self.data.drop(columns=['State', 'RegionCode', 'RegionName',
                                            'Latitude', 'Longitude'])

    def geo_template(self):
        GEO_TEMPLATE = 'Node: E:pcm-dpc->E0\n' +\
                    'typeOf: dcs:EurostatNUTS2\n' +\
                    'dcid: C:pcm-dpc->Location\n\n'
        with open(self.name + '.tmcf', 'w') as f_out:
            f_out.write(GEO_TEMPLATE)
        return 'E:pcm-dpc->E0'


class PcmDpcProvinces(PcmDpc):
    """subclass of provinces data"""
    def __init__(self):
        self.csvpath = ('https://raw.githubusercontent.com/pcm-dpc/COVID-19/'
                        'master/dati-province/dpc-covid19-ita-province.csv')
        self.name = "dpc-covid19-ita-province"
        self.stat_vars = ['CumulativeCount_MedicalConditionIncident_'
                          'COVID_19_PositiveCase']

    def set_location(self):
        province_code_path = ('https://raw.githubusercontent.com/qlj-lijuan/data'
                              '/master/scripts/istat/geos/cleaned/ISTAT_province'
                              '.csv')
        province_code = pd.read_csv(province_code_path)[['Province Abbreviation',
                                                         'NUTS3']]
        province_dict = (province_code.set_index('Province Abbreviation')
                         .to_dict()['NUTS3'])
        # drop the data whose location is "being defined/updated",
        # i.e. ProvinceCode > 111.
        # location Sud Sardegna (Province Code = 111) is not defined as a
        # unique area in DataCommons, skip for now.
        self.data = self.data[self.data['ProvinceCode'] < 111].reset_index()
        self.data['Location'] = self.data['ProvinceAbbreviation'].map(
            province_dict)
        self.data = self.data[['Date', 'Location', 'CumulativeCount_Medical'
                               'ConditionIncident_COVID_19_PositiveCase']]

    def geo_template(self):
        GEO_TEMPLATE = ('Node: E:pcm-dpc->E0\n'
                        'typeOf: dcs:EurostatNUTS3\n'
                        'dcid: C:pcm-dpc->Location\n\n')
        with open(self.name + '.tmcf', 'w') as f_out:
            f_out.write(GEO_TEMPLATE)
        return 'E:pcm-dpc->E0'

def main():
    """process the national, regional, provinces data and generate
    correponding template mcfs"""
    data_obj = [PcmDpcNational(), PcmDpcRegions(), PcmDpcProvinces()]
    for data in data_obj:
        data.preprocess()
        data.generate_tmcf()

if __name__ == "__main__":
    main()
