tab = self.notebook.mainTab
tab.settings['Hessian symmetrisation'] = 'crystal'
#
# SettingsTab
#
tab = self.notebook.settingsTab
tab.settings['Eckart flag'] = False
tab.settings['Neutral Born charges'] = False
tab.settings['Sigma value'] = 5
tab.settings['Mass definition'] = 'program'
#
# 0th Scenario tabs
#
tab = self.notebook.scenarios[0]
tab.settings['Matrix'] = 'ptfe'
tab.settings['Mass or volume fraction'] = 'volume'
tab.settings['Volume fraction'] = 0.01
tab.settings['Ellipsoid a/b'] = 0.5
tab.settings['Unique direction - h'] = 0
tab.settings['Unique direction - k'] = 0
tab.settings['Unique direction - l'] = 1
tab.settings['Effective medium method'] = 'Averaged Permittivity'
tab.settings['Effective medium method'] = 'Mie'
tab.settings['Particle shape'] = 'Sphere'
tab.settings['Particle size(mu)'] = 1.2
tab.settings['Legend'] = 'Averaged permittivity'
# Add new scenarios
methods = ['Maxwell-Garnett', 'Mie']
shapes  = ['Sphere']
hkls    = [[0,0,0]]
vfs     = [0.01, 0.1, 0.2]
sizes   = [0.0, 0.1, 1.2]
#for method in methods:
#    for shape,hkl in zip(shapes,hkls):
#        for vf in vfs:
#            for size in sizes:
#                self.notebook.addScenario()
#                tab = self.notebook.scenarios[-1]
#                tab.settings['Volume fraction'] = vf
#                tab.settings['Particle shape'] = shape
#                tab.settings['Particle size(mu)'] = size
#                tab.settings['Effective medium method'] = method
#                tab.settings['Unique direction - h'] = hkl[0]
#                tab.settings['Unique direction - k'] = hkl[1]
#                tab.settings['Unique direction - l'] = hkl[2]
#                tab.settings['Legend'] = method + ' ' + shape + ' vf='+str(vf)+' size='+str(size)
#
# Plotting Tab
#
tab = self.notebook.plottingTab
tab.settings['Minimum frequency'] = 300
tab.settings['Maximum frequency'] = 800
tab.settings['Frequency increment'] = 0.2
tab.settings['Molar definition'] = 'Unit cells'
tab.settings['Plot title'] = 'Mie method - Castep MgO'
#
# Analysis Tab
#
tab = self.notebook.analysisTab
tab.settings['Minimum frequency'] = -1
tab.settings['Maximum frequency'] = 800
tab.settings['title'] = 'Analysis'
tab.settings['Covalent radius scaling'] = 1.1
tab.settings['Bonding tolerance'] = 0.1
tab.settings['Bar width'] = 0.5
#
