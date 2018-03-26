#!/usr/bin/env python
#
# Copyright 2018 John Kendrick
#
# This file is part of phonona
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the MIT License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# You should have received a copy of the MIT License
# along with this program, if not see https://opensource.org/licenses/MIT
#
"""Phonona driver program to analyse phonons"""
from __future__ import print_function
import math
import os
import sys
import numpy as np
import ctypes
from Python.Constants import amu, PI, avogadro_si, wavenumber, angstrom, isotope_masses, average_masses, covalent_radii
from Python.VaspOutputReader import VaspOutputReader
from Python.PhonopyOutputReader import PhonopyOutputReader
from Python.CastepOutputReader import CastepOutputReader
from Python.GulpOutputReader import GulpOutputReader
from Python.CrystalOutputReader import CrystalOutputReader
from Python.AbinitOutputReader import AbinitOutputReader
from Python.QEOutputReader import QEOutputReader
from Python.ExperimentOutputReader import ExperimentOutputReader
from Python.Plotter import print_reals, print_strings
import Python.Calculator as Calculator

def main():
    """Main Driver routine for Phonona - reads the input and directs the calculation"""
    def show_usage():
        """Show phonona usage"""
        print("phonona ")
        print("         -program castep/crystal/vasp/abinit/qe/phonopy/gulp/experiment")
        print("             Specifies the program that created the files to be processed")
        print("             some programs require two or more files to be specified")
        print("             In the case of VASP file1 must be OUTCAR")
        print("             In the case of CASTEP file1 must be the seed name of the calculation")
        print("             In the case of GULP file1 must be the output file name of the calculation")
        print("             In the case of Crystal file1 must be the output file name of the calculation")
        print("             In the case of Quantum Espresso file1 must be the output file name of the calculation")
        print("             In the case of Abinit file1 must be the output file name of the abinit calculation")
        print("             In the case of phonopy file1 must the qpoints.yaml file")
        print("             In the case of experiment the file should be a file containing experimental information")
        print("         -viewer ")
        print("             Requests a 3D view of the phonon modes")
        print("         -radius element radius")
        print("             Change the value of the covalent radius for the given element")
        print("         -toler tolerance")
        print("             Set the tolerance value used for calculating bonds")
        print("             A bond is created betweem two atoms whose distance apart ")
        print("             is less than scale*(radi+radj)+toler ")
        print("             The default value of toler is 0.1    ")
        print("         -scale scale")
        print("             Set the scale factor used for calculating bonds")
        print("             The default value of scale is 1.1    ")
        print("         -masses program")
        print("             By default the atomic masses are defined by the average weight")
        print("             The options are program/average/isotope           ")
        print("             average means the weight is averaged using the natural abundance")
        print("             isotope means the most abundant isotopic mass is used")
        print("             program means that the QM/MM programs masses are used")
        print("         -mass element symbol")
        print("             Allows individual elements to have their masses defined")
        print("             the -masses mass definition is applied first,     ")
        print("             then any masses defined by -mass are applied,     ")
        print("         -csv file.csv")
        print("           print a csv file")
        print("         -excel  file.xlsx")
        print("           output the results to an excel file")
        print("         -vmax vmax  report all frequencies from vmin to vmax")
        print("         -vmin vmin  report all frequencies from vmin to vmax")
        print("         -ignore mode")
        print("             Ignore a mode in the construction of the dielectric")
        print("             by default all modes with a frequency less than 5cm-1 are ignored")
        print("             -ignore (can be used more than once) is used only modes specified are ignored")
        print("         -mode  index  only include this mode in the sum")
        print("             This option can be included several times")
        print("             By default all frequencies are included")
        print("         -eckart")
        print("             The translational modes will be projected from the dynamical matrix")
        print("             This option only applies when the dynmical matrix is read and used")
        print("             to calculate the frequencies and normal modes.")
        print("         -neutral")
        print("             Charge neutrality of the Born charges is enforced")
        print("         -hessian [crystal|symm]")
        print("             By default the hessian is symmetrised by forming 0.5 * ( Ht + H )")
        print("             however the crystal package symmetrises by making the upper triangle the same as the lower")
        print("             For compatibility -hessian crystal will symmetrise in the same way as the Crystal package")
        print("         -help to print out this help information")
        print("         -h    to print out this help information")
        return

    # define some constants which may change due to the parameters on the command line
    debug          = False
    program        = ""
    qmprogram      = ""
    names          = []
    my_modes       = []
    ignore_modes   = []
    mass_dictionary= {}
    vmax           = 9000.0
    vmin           = 0.0
    scale          = 1.1
    toler          = 0.1
    mass_definition = 'average'
    eckart = False
    neutral = False
    print_info     = False
    csvfile        = ""
    excelfile      = ""
    hessian_symmetrisation = "symm"
    viewer3D = False

    # check usage
    if len(sys.argv) <= 1:
        show_usage()
        exit()

    # Begin processing of command line
    command_line = ' '.join(sys.argv)
    tokens = sys.argv[1:]
    ntokens = len(tokens)
    itoken = 0
    while itoken < ntokens:
        token = tokens[itoken]
        if token == "-program":
            itoken += 1
            program = tokens[itoken]
            if program == "phonopy":
                itoken += 1
                qmprogram = tokens[itoken]
        elif token == "-viewer":
            viewer3D = True
        elif token == "-mass":
            itoken += 1
            element = tokens[itoken]
            itoken += 1
            mass = float(tokens[itoken])
            mass_dictionary[element] = mass
        elif token == "-masses":
            itoken += 1
            if tokens[itoken][0] == "p":  mass_definition = "program"
            if tokens[itoken][0] == "a":  mass_definition = "average"
            if tokens[itoken][0] == "i":  mass_definition = "isotope"
        elif token == "-toler":
            itoken += 1
            toler = float(tokens[itoken])
        elif token == "-scale":
            itoken += 1
            scale = float(tokens[itoken])
        elif token == "-radius":
            itoken += 1
            element = tokens[itoken].capitalize()
            itoken += 1
            new_radius = float(tokens[itoken])
            if element in covalent_radii:
                covalent_radii[element] = new_radius
                print("The covalent radius of ",element," is now ", new_radius)
            else:
                print("Error in specifying the element",element)
                exit()
        elif token == "-mode":
            itoken += 1
            my_modes.append(int(tokens[itoken]))
        elif token == "-ignore":
            itoken += 1
            ignore_modes.append(int(tokens[itoken]))
        elif token == "-vmin":
            itoken += 1
            vmin = float(tokens[itoken])
        elif token == "-vmax":
            itoken += 1
            vmax = float(tokens[itoken])
        elif token == "-csv":
            itoken += 1
            csvfile = tokens[itoken]
        elif token == "-excel":
            itoken += 1
            excelfile = tokens[itoken]
        elif token == "-eckart":
            eckart = True
        elif token == "-hessian":
            itoken += 1
            token = tokens[itoken]
            if token == "crystal":
                hessian_symmetrisation = token
            elif token == "symm":
                hessian_symmetrisation = token
            else:
                print("The -hessian directive must be qualified with \"symm\" or \"crystal\" {:s}".format(token))
                exit(1)
        elif token == "-neutral":
            neutral = True
        elif token == "-h":
            show_usage()
            exit()
        elif token == "-help":
            show_usage()
            exit()
        elif token == "-debug":
            debug = True
        elif token[0] == "-":
            print("Error on input unkown option: {:s}".format(token))
            exit(1)
        else:
            names.append(token)
        itoken += 1
        # end loop over tokens

    # Look for obvious errors
    programs = ["castep", "abinit", "qe", "castep", "vasp", "crystal", "gulp", "phonopy", "experiment"]
    if program is not "":
        if program not in programs:
            print("program specified is: {:s}".format(program))
            print("Needs to be one of: " + " ".join(p for p in programs))
            exit(1)
    if qmprogram is not "":
        if qmprogram not in programs:
            print("QM program specified is: {:s}".format(program))
            print("Needs to be one of: " + " ".join(p for p in programs))
            exit(1)
    if len(names) <= 0:
        print("No files were specified")
        show_usage()
        exit(1)

    fd_excelfile = None
    fd_csvfile = None
    if csvfile != "":
        print("Creating a csv file: "+csvfile)
        fd_csvfile = open(csvfile, 'w')
    if excelfile != "":
        print("Creating an excel file: "+excelfile)
        fd_excelfile = 1
    print("Vmin is: {:7.1f} cm-1".format(vmin))
    print("Vmax is: {:7.1f} cm-1".format(vmax))
    if len(my_modes) > 0:
        print("Only consider contributions from phonon modes:" + " ".join(str(m) for m in my_modes))
    else:
        if len(ignore_modes) > 0:
            print("Ignoring the following phonon modes:")
            print("     " + " ".join("{:d}".format(m) for m in ignore_modes))
        else:
            print("All phonon modes will be considered")
    #
    # Arrays will be used where possible from now on, also some arrays will contain complex numbers
    #
    reader = None
    if program == "":
        #  This is the old behaviour.  It copes with VASP, CASTEP and Crystal
        #  If names[0] is a directory then we will use a vaspoutputreader
        #  Otherwise it is a seedname for castep, or a gulp output file, or a crystal output file
        if os.path.isdir(names[0]):
            print('Analysing VASP directory: {} '.format(names[0]))
            outcarfile = os.path.join(names[0], "OUTCAR")
            kpointsfile = os.path.join(names[0], "KPOINTS")
            if not os.path.isfile(outcarfile):
                print("Error: NO OUTCAR FILE IN DIRECTORY")
                exit()
            reader = VaspOutputReader( [outcarfile, kpointsfile] )
        elif names[0].find("OUTCAR") >= 0 and os.path.isfile("OUTCAR"):
            reader = VaspOutputReader(names)
        elif names[0].find(".gout") >= 0 and os.path.isfile(names[0]):
            reader = GulpOutputReader(names)
        elif names[0].find(".out") >= 0 and os.path.isfile(names[0]):
            reader = CrystalOutputReader(names)
        elif names[0].find(".castep") >= 0 and os.path.isfile(names[0]):
            reader = CastepOutputReader(names)
        elif os.path.isfile(names[0]+".castep") and os.path.isfile(names[0]+".castep"):
            reader = CastepOutputReader([names[0]+".castep"])
        else:
            print('No valid file name has been found on the command line')
            print('Try using the -program option to specify the')
            print('files which will be read')
            exit(1)
    else:
        # New Specification of Program used to define the input files
        # Abinit and QE need a couple of files to be specified
        #
        # First Check that the file(s) we requested are there
        #
        checkfiles = []
        if program == "castep":
            if names[0].find(".castep") >= 0:
                seedname, ext = os.path.splitext(names[0])
            else:
                seedname = names[0]
            checkfiles.append(seedname+".castep")
        elif program == "phonopy":
            # We only have a VASP / Phonopy interface
            # Creat a list of phonopy files
            pnames = []
            head,tail = os.path.split(names[0])
            pnames.append(head+'qpoints.yaml')
            pnames.append(head+'phonopy.yaml')
            # Creat a list of VASP files NB.  They all have to be in the same directory
            vnames = names
            pnames.extend(vnames)
            checkfiles = pnames
        else:
            checkfiles = names
        print("")
        print("Program used to perform the phonon calculation was: {}".format(program))
        for f in checkfiles:
            print("The file containing the output is: {}".format(f))
            if not os.path.isfile(f):
                print("Output files created by program: {}".format(program))
                print("Error: file not available: {}".format(f))
                exit()
        # The files requested are available so read them
        if program == "castep":
            reader = CastepOutputReader(names)
        elif program == "vasp":
            reader = VaspOutputReader(names)
        elif program == "gulp":
            reader = GulpOutputReader(names)
        elif program == "crystal":
            reader = CrystalOutputReader(names)
        elif program == "abinit":
            reader = AbinitOutputReader(names)
        elif program == "qe":
            reader = QEOutputReader(names)
        elif program == "phonopy":
            # Which QM program was used by PHONOPY?
            if qmprogram == "castep":
                qmreader = CastepOutputReader(vnames)
            elif qmprogram == "vasp":
                qmreader = VaspOutputReader(vnames)
            elif qmprogram == "gulp":
                qmreader = GulpOutputReader(vnames)
            elif qmprogram == "crystal":
                qmreader = CrystalOutputReader(vnames)
            elif qmprogram == "abinit":
                qmreader = AbinitOutputReader(vnames)
            elif qmprogram == "qe":
                qmreader = QEOutputReader(vnames)
            # The QM reader is used to get info about the QM calculation
            reader = PhonopyOutputReader(pnames,qmreader)
        elif program == "experiment":
            reader = ExperimentOutputReader(names)
        # endif
    # end if
    if eckart:
        print("The translational modes will be projected from the Dynamical matrix where possible")
    else:
        print("No projection of the dynamical matrix will be performed")
    if neutral:
        print("The charge neutrality of the Born atomic charges will be enforced")
    else:
        print("The charge neutrality of the Born atomic charges will not be enforced")
    # Modify the default settings of the reader
    reader.hessian_symmetrisation = hessian_symmetrisation
    reader.debug = debug
    # Initiate reading of the files
    reader.read_output()
    reader.eckart = eckart
    if neutral:
        reader.neutralise_born_charges()
    if print_info:
        reader.print_info()
    # What mass definition are we using?
    if not mass_definition == "program" or mass_dictionary:
        print(" ")
        print("Atomic masses will be defined using: ", mass_definition)
        if mass_dictionary:
            print("Additional elemental masses have been specifically specified:")
            for element in mass_dictionary:
                print("    ",element,": ",mass_dictionary[element])
        if debug:
           print_reals("Old masses by atom types", reader.masses_per_type,format="{:10.6f}")
           print_reals("Old atomic mass list", reader.masses,format="{:10.6f}")
        if mass_definition == "average":
            reader.change_masses(average_masses, mass_dictionary)
        elif mass_definition == "isotope":
            reader.change_masses(isotope_masses, mass_dictionary)
        if debug:
            print_reals("New masses by atom types", reader.masses_per_type,format="{:10.6f}")
            print_reals("New atomic mass list", reader.masses,format="{:10.6f}")
    else:
        print(" ")
        print("Atomic masses will be defined using: ", mass_definition)
        if debug:
            print_reals("Masses by atom types", reader.masses_per_type,format="{:10.6f}")
            print_reals("Atomic mass list", reader.masses,format="{:10.6f}")
    # access the information as numpy arrays.  Use atomic units for these arrays
    masses = np.array(reader.masses) * amu
    print("")
    print("Volume of unit cell is {:14.8f} Angstrom^3".format(reader.volume))
    mtotal = 0.0
    atom_masses = []
    for mass in reader.masses:
        atom_masses.append(mass)
        mtotal = mtotal + mass
    print("Total unit cell mass is: {:14.8f} g/mol".format(mtotal))
    crystal_density = mtotal/(avogadro_si * reader.volume * 1.0e-24)
    print("Crystal density is: {:9.5f} g/cc".format(crystal_density))
    rho1 = crystal_density
    print("")
    if fd_excelfile is not None:
        import xlsxwriter as xlsx
        workbook = xlsx.Workbook(excelfile)
        worksheet = workbook.add_worksheet('info')
        excel_row = 0;  worksheet.write(excel_row,0,command_line)
        excel_row += 2; worksheet.write(excel_row,0,'Volume of unit cel (Angstrom^3)')
        excel_row += 1; worksheet.write(excel_row,0,reader.volume)
        excel_row += 2; worksheet.write(excel_row,0,'Unit cell mass (g/mol)')
        excel_row += 1; worksheet.write(excel_row,0,mtotal)
        excel_row += 2; worksheet.write(excel_row,0,'Crystal density (g/cc)')
        excel_row += 1; worksheet.write(excel_row,0,crystal_density)
    # Get the born charges
    born_charges = np.array(reader.born_charges)
    #
    # Ask the reader to calculate the massweighted normal modes
    # This call allows the projection to be performed if necessary
    #
    mass_weighted_normal_modes = reader.calculate_mass_weighted_normal_modes()
    frequencies_cm1 = np.array(reader.frequencies)
    frequencies = frequencies_cm1 * wavenumber
    volume = reader.volume*angstrom*angstrom*angstrom
    mode_list = []
    # set the widths and define the list of modes to me considered
    for imode, frequency in enumerate(reader.frequencies):
        mode_list.append(imode)

    if debug:
        print("Complete mode list is: " + ",".join("{:4d}".format(m) for m in mode_list))
    if program == 'experiment':
        oscillator_strengths = reader.oscillator_strengths
    else:
        #
        # calculate normal modes in xyz coordinate space
        # should they be re-normalised or not?  According to Balan the mass weighted coordinates should be normalised
        normal_modes = Calculator.normal_modes(masses, mass_weighted_normal_modes)
        # from the normal modes and the born charges calculate the oscillator strengths of each mode
        oscillator_strengths = Calculator.oscillator_strengths(normal_modes, born_charges)
    # calculate the intensities from the trace of the oscillator strengths
    intensities = Calculator.infrared_intensities(oscillator_strengths)
    if fd_excelfile is not None:
        excel_row += 2; worksheet.write(excel_row,0,'Transverse optical frequencies (cm-1)')
        excel_row += 1; [ worksheet.write(excel_row,col,f) for col,f in enumerate(np.real(frequencies_cm1)) ]

    cell = reader.unit_cells[-1]
    cell.set_atomic_masses(atom_masses)
    newcell,nmols,old_order = cell.calculate_molecular_contents(scale, toler, covalent_radii)
    newcell.printInfo()
    # Reorder the atoms so that the mass weighted normal modes order agrees with the ordering in the new cell
    nmodes,nions,temp = np.shape(normal_modes)
    new_normal_modes = np.zeros( (nmodes,3*nions) )
    new_mass_weighted_normal_modes = np.zeros( (nmodes,3*nions) )
    masses = newcell.atomic_masses
    for imode,mode in enumerate(mass_weighted_normal_modes):
        for index,old_index in enumerate(old_order):
            i = index*3
            j = old_index*3
            new_mass_weighted_normal_modes[imode,i+0] = mode[old_index][0] 
            new_mass_weighted_normal_modes[imode,i+1] = mode[old_index][1] 
            new_mass_weighted_normal_modes[imode,i+2] = mode[old_index][2] 
            new_normal_modes[imode,i+0] = new_mass_weighted_normal_modes[imode,i+0] / math.sqrt(masses[index])
            new_normal_modes[imode,i+1] = new_mass_weighted_normal_modes[imode,i+1] / math.sqrt(masses[index])
            new_normal_modes[imode,i+2] = new_mass_weighted_normal_modes[imode,i+2] / math.sqrt(masses[index])
    # Calculate the distribution in energy for the normal modes
    mode_energies = Calculator.calculate_energy_distribution(newcell, frequencies_cm1, new_mass_weighted_normal_modes)
    # Output the final result
    title = ['Freq(cm-1)','%mol-cme','%mol-rot','%vib']
    for i in range(nmols):
        title.append('%mol-'+str(i))
    print_strings('Percentage energies in vibrational modes',title,format="{:>10}")
    if not fd_csvfile is None:
        print_strings('Percentage energies in vibrational modes',title,format="{:>10}",file=fd_csvfile,separator=",")
    for freq,energies in zip(frequencies_cm1,mode_energies):
           tote,cme,rote,vibe,molecular_energies = energies
           output = [ freq, 100*cme/tote, 100*rote/tote, 100*vibe/tote ]
           for e in molecular_energies:
               output.append(100*e/tote)
           print_reals('',output,format="{:10.2f}")
           if not fd_csvfile is None:
               print_reals('',output,format="{:10.2f}",file=fd_csvfile,separator=",")
    # if using a excel file write out the results
    if not fd_excelfile is None:
        excel_row += 2; worksheet.write(excel_row,0,'Percentage energies in vibrational modes')
        excel_row += 1; [ worksheet.write(excel_row,col,f) for col,f in enumerate(title) ]
        for freq,energies in zip(frequencies_cm1,mode_energies):
           tote,cme,rote,vibe, molecular_energies = energies
           output = [ freq, 100*cme/tote, 100*rote/tote, 100*vibe/tote ]
           for e in molecular_energies:
               output.append(100*e/tote)
           excel_row += 1; [ worksheet.write(excel_row,col,f) for col,f in enumerate( output ) ]
    if fd_excelfile is not None:
        workbook.close()
    if fd_csvfile is not None:
        fd_csvfile.close()
    if viewer3D:
        from Python.ViewerClass import ViewerClass
        viewer = ViewerClass(newcell,new_normal_modes,frequencies_cm1)
        viewer.configure_traits()

if __name__ == "__main__":
    main()