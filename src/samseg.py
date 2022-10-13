#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 14:25:40 2021

@author: ColinVDB
SAMSEG
"""


import sys
import os
from os.path import join as pjoin
from os.path import exists as pexists
# from dicom2bids import *
from PyQt5.QtCore import (QSize,
                          Qt,
                          QModelIndex,
                          QMutex,
                          QObject,
                          QThread,
                          pyqtSignal,
                          QRunnable,
                          QThreadPool)
from PyQt5.QtWidgets import (QDesktopWidget,
                             QApplication,
                             QWidget,
                             QPushButton,
                             QMainWindow,
                             QLabel,
                             QLineEdit,
                             QVBoxLayout,
                             QHBoxLayout,
                             QFileDialog,
                             QDialog,
                             QTreeView,
                             QFileSystemModel,
                             QGridLayout,
                             QPlainTextEdit,
                             QMessageBox,
                             QListWidget,
                             QTableWidget,
                             QTableWidgetItem,
                             QMenu,
                             QAction,
                             QTabWidget,
                             QCheckBox)
from PyQt5.QtGui import (QFont,
                         QIcon)
import subprocess
import shutil
import nibabel as nib

# faulthandler.enable()

def launch(parent, add_info=None):
    """
    

    Parameters
    ----------
    parent : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    window = MainWindow(parent, add_info)
    window.show()
    # if not QApplication.instance():
    #     app = QApplication(sys.argv)
    # else:
    #     app = QApplication.instance()

    # # app = QApplication(sys.argv)

    # window = MainWindow(parent)

    # window.show()

    # app.exec()
    
    

# =============================================================================
# MainWindow
# =============================================================================
class MainWindow(QMainWindow):
    """
    """
    

    def __init__(self, parent, add_info):
        """
        

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        self.add_info = add_info

        self.setWindowTitle("SAMSEG")
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.center()
        
        self.tab = SamsegTab(self, self.add_info)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab)

        self.window.setLayout(self.layout)


    def center(self):
        """
        

        Returns
        -------
        None.

        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())



# =============================================================================
# SamsegTab
# =============================================================================
class SamsegTab(QWidget):
    """
    """
    

    def __init__(self, parent, add_info):
        """
        

        Parameters
        ----------
        parent : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__()
        self.parent = parent
        self.bids = self.parent.bids
        self.add_info = add_info
        self.setMinimumSize(500, 200)
        
        self.mprage_check = QCheckBox('MPRAGE')
        self.mprage_check.stateChanged.connect(self.mprage_clicked)
        self.mprage = False
        
        self.flair_check = QCheckBox('FLAIR')
        self.flair_check.stateChanged.connect(self.flair_clicked)
        self.flair = False
        
        self.normalization_check = QCheckBox('Normalization')
        self.normalization_check.stateChanged.connect(self.normalization_clicked)
        self.normalization = False
        
        # self.preprocessing_check = QCheckBox('Preprocessing')
        # self.preprocessing_check.stateChanged.connect(self.preprocessing_clicked)
        # self.preprocessing = False
        
        self.subjects_input = QLineEdit(self)
        self.subjects_input.setPlaceholderText("Select subjects")

        self.sessions_input = QLineEdit(self)
        self.sessions_input.setPlaceholderText("Select sessions")
        
        self.samseg_button = QPushButton("Run Segmentation")
        self.samseg_button.clicked.connect(self.samseg_computation)
        
        layout = QVBoxLayout()
        layout.addWidget(self.mprage_check)
        layout.addWidget(self.flair_check)
        layout.addWidget(self.normalization_check)
        # layout.addWidget(self.preprocessing_check)
        layout.addWidget(self.subjects_input)
        layout.addWidget(self.sessions_input)
        layout.addWidget(self.samseg_button)
        
        self.setLayout(layout)
        
    
    def normalization_clicked(self, state):
        if state == Qt.Checked:
            self.normalization = True
        else:
            self.normalization = False
            
    
    def mprage_clicked(self, state):
        if state == Qt.Checked:
            self.mprage = True
        else:
            self.mprage = False
            
            
    def flair_clicked(self, state):
        if state == Qt.Checked:
            self.flair = True
        else:
            self.flair = False
            
            
    # def preprocessing_clicked(self, state):
    #     if state == Qt.Checked:
    #         self.preprocessing = True
    #     else:
    #         self.preprocessing = False
            
        

    def samseg_computation(self):
        """
        

        Returns
        -------
        None.

        """
        subjects = self.subjects_input.text()
        sessions = self.sessions_input.text()
        self.subjects = []
        # find subjects
        if subjects == 'all':
            all_directories = [x for x in next(os.walk(self.bids.root_dir))[1]]
            for sub in all_directories:
                if sub.find('sub-') == 0:
                    self.subjects.append(sub.split('-')[1])
        else:
            subjects_split = subjects.split(',')
            for sub in subjects_split:
                if '-' in sub:
                    inf_bound = sub.split('-')[0]
                    sup_bound = sub.split('-')[1]
                    fill = len(inf_bound)
                    inf = int(inf_bound)
                    sup = int(sup_bound)
                    for i in range(inf,sup+1):
                        self.subjects.append(str(i).zfill(fill))
                else:
                    self.subjects.append(sub)

        # find sessions
        self.sessions = []
        if sessions == 'all':
            self.sessions.append('all')
        else:
            sessions_split = sessions.split(',')
            for ses in sessions_split:
                if '-' in ses:
                    inf_bound = ses.split('-')[0]
                    sup_bound = ses.split('-')[1]
                    fill = len(inf_bound)
                    inf = int(inf_bound)
                    sup = int(sup_bound)
                    for i in range(inf, sup+1):
                        self.sessions.append(str(i).zfill(fill))
                else:
                    self.sessions.append(ses)

        self.subjects_and_sessions = []
        for sub in self.subjects:
            if len(self.sessions) != 0:
                if self.sessions[0] == 'all':
                    all_directories = [x for x in next(os.walk(pjoin(self.bids.root_dir,f'sub-{sub}')))[1]]
                    sub_ses = []
                    for ses in all_directories:
                        if ses.find('ses-') == 0:
                            sub_ses.append(ses.split('-')[1])
                    self.subjects_and_sessions.append((sub,sub_ses))
                else:
                    self.subjects_and_sessions.append((sub,self.sessions))
                         
        self.thread = QThread()
        self.action = SamSegWorker(self.bids, self.add_info, self.subjects_and_sessions, mprage=self.mprage, flair=self.flair, normalization=self.normalization, preprocessing=True)
        self.action.moveToThread(self.thread)
        self.thread.started.connect(self.action.run)
        self.action.in_progress.connect(self.is_in_progress)
        self.action.finished.connect(self.thread.quit)
        self.action.finished.connect(self.action.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        
        self.parent.hide()
        
        
    def is_in_progress(self, in_progress):
        self.parent.parent.work_in_progress.update_work_in_progress(in_progress)



# =============================================================================
# LesVolLocSegWorker
# =============================================================================
class SamSegWorker(QObject):
    finished = pyqtSignal()
    in_progress = pyqtSignal(tuple)

    def __init__(self, bids, add_info, subjects_and_sessions, mprage=False, flair=False, normalization=False, preprocessing=False):
        """
        
        
        Parameters
        ----------
        bids : TYPE
          DESCRIPTION.
        sub : TYPE
          DESCRIPTION.
        ses : TYPE
          DESCRIPTION.
        normalization : TYPE #True to decrease images resolution
          DESCRIPTION.
        mprage : TYPE        #True if mprage available
          DESCRIPTION.
        step1 : TYPE         #True to execute the preprocessing part
          DESCRIPTION.
        step2 : TYPE         #True to execute SAMSEG segmentation: Produce lesion probability mask
          DESCRIPTION.
        step3 : TYPE         #True to binarize the lesion probability mask
          DESCRIPTION.
        
        Returns
        -------
        None.
        
        """
        super().__init__()
        self.bids = bids
        self.add_info = add_info
        self.subjects_and_sessions = subjects_and_sessions
        self.normalization = normalization 
        self.mprage = mprage 
        self.flair = flair              
        self.preprocessing = preprocessing           
        self.pipeline = "SAMSEG"
        
        
    def run(self):
        self.in_progress.emit((self.pipeline, True))
        
        for sub, sess in self.subjects_and_sessions:
            for ses in sess:
                self.sub = sub
                self.ses = ses
                print(f'Running LesVolLoc for sub-{sub} ses-{ses}')
                # self.run_LesVolLoc()
                
                # Define paths and filenames for a certain SUBJECT and SESSION
                segment = 'segmentation'
                transfo = 'transformation'
                sub_ses_directory = pjoin(self.bids.root_dir, f'sub-{self.sub}', f'ses-{self.ses}', 'anat')
                flair = f'sub-{self.sub}_ses-{self.ses}_{self.add_info.get("flair")}.nii.gz'
                mprage = f'sub-{self.sub}_ses-{self.ses}_{self.add_info.get("mprage")}.nii.gz'
                sub_ses_derivative_path_segment = pjoin(self.bids.root_dir, 'derivatives', self.pipeline, f'sub-{self.sub}', f'ses-{self.ses}', segment)
                sub_ses_derivative_path_transfo = pjoin(self.bids.root_dir, 'derivatives', self.pipeline, f'sub-{self.sub}', f'ses-{self.ses}', transfo)
                
                # Define list of directories to create
                directorysegment = [pjoin('derivatives', self.pipeline), pjoin('derivatives', self.pipeline, f'sub-{self.sub}'), pjoin('derivatives', self.pipeline, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', self.pipeline, f'sub-{self.sub}', f'ses-{self.ses}', segment)]
                directorytransfo = [pjoin('derivatives', self.pipeline), pjoin('derivatives', self.pipeline, f'sub-{self.sub}'), pjoin('derivatives', self.pipeline, f'sub-{self.sub}', f'ses-{self.ses}'), pjoin('derivatives', self.pipeline, f'sub-{self.sub}', f'ses-{self.ses}', transfo)]

                # Perform Lesion Segmentation, Localisation and Volumetry
                
                ## Step1 : Preprocessing (normalization and registration FLAIR and MPRAGE)
                if self.preprocessing: 
                    
                    print('Start Preprocessing...')
                    
                    # Pre check
                    ## Create corresponding directory if necessary
                    self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorytransfo)
                    
                    # Actions
                    ## Normalization if need 
                    if self.normalization:
                        
                        print('normalization')
                        
                        # Pre check
                        ## check if preprocessing has already been done previously, and delete the results if necessary
                        if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed')):
                            shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed'))
                        if pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                            os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                        
                        if self.flair:    
                            ## check if files exist
                            if not pexists(pjoin(sub_ses_directory, flair)):
                                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                                self.end_run()
                                return
                            
                            # Actions
                            ## Normalized FLAIR
                            try:
                                print(f'Resizing FLAIR for sub-{self.sub} ses-{self.ses}...')
                                
                                subprocess.Popen(f'recon-all -motioncor -i {sub_ses_directory}/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed -sd {sub_ses_derivative_path_transfo}', shell=True).wait()
                                # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_directory}:/media/sub_ses_directory -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && recon-all -motioncor -i /media/sub_ses_directory/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed -sd /media/sub_ses_derivative_path_transfo"', shell=True).wait()
                                
                            except Exception as e:
                                print(f'[ERROR] - {self.pipeline} | {e} when resizing FLAIR for sub-{self.sub}_ses-{self.ses}!')
                                self.end_run()
                                return
                            
                            ## Convert mgz file from freesurfer to nii file 
                            try:
                                print(f'Converting FLAIR_used.mgz to .nii.gz for sub-{self.sub} ses-{self.ses}...')
                                
                                subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed/mri/orig.mgz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz', shell=True).wait()
                                # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed/mri/orig.mgz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz"', shell=True).wait()           
                                
                            except Exception as e:
                                print(f'[ERROR] - {self.pipeline} | {e} when converting FLAIR_used.mgz to .nii.gz for sub-{self.sub}_ses{self.ses}!')
                                return
                            
                        if self.mprage:    
                            ## check if files exist
                            if not pexists(pjoin(sub_ses_directory, mprage)):
                                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, mprage)}" not Found !')
                                self.end_run()
                                return
                            
                            # Actions
                            ## Normalized FLAIR
                            try:
                                print(f'Resizing MPRAGE for sub-{self.sub} ses-{self.ses}...')
                                
                                subprocess.Popen(f'recon-all -motioncor -i {sub_ses_directory}/{mprage} -subjid sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed -sd {sub_ses_derivative_path_transfo}', shell=True).wait()
                                # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_directory}:/media/sub_ses_directory -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && recon-all -motioncor -i /media/sub_ses_directory/{flair} -subjid sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed -sd /media/sub_ses_derivative_path_transfo"', shell=True).wait()
                                
                            except Exception as e:
                                print(f'[ERROR] - {self.pipeline} | {e} when resizing MPRAGE for sub-{self.sub}_ses-{self.ses}!')
                                self.end_run()
                                return
                            
                            ## Convert mgz file from freesurfer to nii file 
                            try:
                                print(f'Converting MPRAGE_used.mgz to .nii.gz for sub-{self.sub} ses-{self.ses}...')
                                
                                subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed/mri/orig.mgz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz', shell=True).wait()
                                # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed/mri/orig.mgz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz"', shell=True).wait()           
                                
                            except Exception as e:
                                print(f'[ERROR] - {self.pipeline} | {e} when converting FLAIR_used.mgz to .nii.gz for sub-{self.sub}_ses{self.ses}!')
                                self.end_run()
                                return
                        
                    ## No normalization
                    else: 
                        
                        print('No Normalization !')
                        
                        # Pre check
                        ## check if preprocessing has already been done previously, and delete the results if necessary
                        if os.path.isdir(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed')):
                            shutil.rmtree(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed'))
                        if pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                            os.remove(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                        
                        if self.flair:
                            
                            ## check if files exist
                            if not pexists(pjoin(sub_ses_directory, flair)):
                                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                                self.end_run()
                                return
                            
                            # Actions
                            ## Copy FLAIR in directory of transformations for access simplicity
                            shutil.copyfile(pjoin(sub_ses_directory, flair), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz'))
                            
                        if self.mprage:    
                        
                            ## check if files exist
                            if not pexists(pjoin(sub_ses_directory, mprage)):
                                print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, mprage)}" not Found !')
                                self.end_run()
                                return
                            
                            # Actions
                            ## Copy FLAIR in directory of transformations for access simplicity
                            shutil.copyfile(pjoin(sub_ses_directory, mprage), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                            
                    
                    ## Register FLAIR on MPRAGE
                    if self.mprage and self.flair:
                        
                        print('Registering FLAIR on MPRAGE...')
                        
                        # Pre check
                        ## check if files exist
                        if not pexists(pjoin(sub_ses_directory, flair)):
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, flair)}" not Found !')
                            self.end_run()
                            return
                        
                        if not pexists(pjoin(sub_ses_directory, mprage)):
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{pjoin(sub_ses_directory, mprage)}" not Found !')
                            self.end_run()
                            return
                        
                        
                        # Actions
                        ## Resgistering MPRAGE on FLAIR
                        try:
                            print(f'Registration of FLAIR on MPRAGE for sub-{self.sub} ses-{self.ses}...')
                                                 
                            # subprocess.Popen(f'$ANTs_registration -d 3 -n 4 -f {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -m {sub_ses_directory}/{mprage} -t r -o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed', shell=True).wait()
                            # subprocess.Popen(f'docker run --rm --privileged -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_directory}:/media/sub_ses_directory colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && \$ANTs_registration -d 3 -n 4 -f /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz -m /media/sub_ses_directory/{mprage} -t r -o /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed"', shell=True).wait()      
                            
                            subprocess.Popen(f'mri_coreg --mov {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz --ref {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz --reg flairToT1.lta', shell=True).wait()
                            subprocess.Popen(f'mri_vol2vol --mov {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz --reg flairToT1.lta --o {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_registered.nii.gz --targ {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz', shell=True).wait()                                
                            
                            # Change the name of registration output
                            # shutil.move(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessedWarped.nii.gz'), pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz'))
                        
                        except Exception as e:
                            print(f'[ERROR] - {self.pipeline} | {e} during registration of FLAIR on MPRAGE for sub-{self.sub}_ses{self.ses}!')
                            self.end_run()
                            return
                        
                    else:
                        pass
                    
                    print('End Preprocessing!')
                       
                else:
                    pass
                
                
                ## Step2 : Segmentation using SAMSEG to compute lesion probability mask
                    
                print('Start Segmentating lesions with SAMSEG...')
                
                # Pre check
                ## Create segmentation directories
                self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = directorysegment)     
                self.bids.mkdirs_if_not_exist(self.bids.root_dir, directories = [f'{sub_ses_derivative_path_segment}/SAMSEG_results'])
                
                # Actions
                ## Run SAMSEG with FLAIR and MPRAGE
                if self.mprage and self.flair:
                    
                    print('Segmenting with FLAIR & mprage')
                    
                    # Pre check
                    ## check if files exist
                    if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_registered.nii.gz')):
                        file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_registered.nii.gz')
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                        self.end_run()
                        return
                    
                    if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                        file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')
                        print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                        self.end_run()
                        return
                    
                    # Actions
                    try:
                        print(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
                        
                        subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_registered.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_registered.mgz', shell=True).wait()
                        # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz"', shell=True).wait()
                        
                        subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz', shell=True).wait()
                        # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz"', shell=True).wait()
                        
                        subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_registered.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                        # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && run_samseg -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 1 --threads 4 -o /media/sub_ses_derivative_path_segment/SAMSEG_results --save-posteriors"', shell=True).wait()
                        
                        subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                        # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_segment/SAMSEG_results/posteriors/Lesions.mgz /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz"', shell=True).wait()
                        
                    except Exception as e:
                        print(f'[ERROR] - {self.pipeline} | {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
                        self.end_run()
                        return
                    
                ## Run SAMSEG with only FLAIR 
                else:
                    
                    if self.flair:
                    
                        print('Segmenting with only FLAIR')
                        
                        # Pre check
                        ## check if files exist
                        if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')):
                            file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz')
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                            self.end_run()
                            return
                        
                        # Actions
                        try:
                            print(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
    
                            subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz', shell=True).wait()
                            # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz"', shell=True).wait()
                            
                            subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                            # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && run_samseg -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o /media/sub_ses_derivative_path_segment/SAMSEG_results --save-posteriors"', shell=True).wait()
                            
                            subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                            # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_segment/SAMSEG_result/posteriors/Lesions.mgz /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz"', shell=True).wait()
                            
                        except Exception as e:   
                            print(f'[ERROR] - {self.pipeline} | {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
                            self.end_run()
                            return
                    
                    if self.mprage:
                        print('Segmenting with only MPRAGE')
                        
                        # Pre check
                        ## check if files exist
                        if not pexists(pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')):
                            file = pjoin(sub_ses_derivative_path_transfo, f'sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz')
                            print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                            self.end_run()
                            return
                        
                        # Actions
                        try:
                            print(f'Running Samseg for sub-{self.sub} ses-{self.ses}...')
    
                            subprocess.Popen(f'mri_convert {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.nii.gz {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz', shell=True).wait()
                            # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.nii.gz /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz"', shell=True).wait()
                            
                            subprocess.Popen(f'run_samseg -i {sub_ses_derivative_path_transfo}/sub-{self.sub}_ses-{self.ses}_MPRAGE_preprocessed.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o {sub_ses_derivative_path_segment}/SAMSEG_results --save-posteriors', shell=True).wait()
                            # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_transfo}:/media/sub_ses_derivative_path_transfo -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && run_samseg -i /media/sub_ses_derivative_path_transfo/sub-{self.sub}_ses-{self.ses}_FLAIR_preprocessed.mgz --lesion --lesion-mask-pattern 0 --threads 4 -o /media/sub_ses_derivative_path_segment/SAMSEG_results --save-posteriors"', shell=True).wait()
                            
                            subprocess.Popen(f'mri_convert {sub_ses_derivative_path_segment}/SAMSEG_results/posteriors/Lesions.mgz {sub_ses_derivative_path_segment}/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz', shell=True).wait()
                            # subprocess.Popen(f'docker run --rm --privileged -v {self.freesurfer_license}:/programs/freesurfer/license.txt -v {sub_ses_derivative_path_segment}:/media/sub_ses_derivative_path_segment colinvdb/bmat-ext:0.0.1 /bin/bash -c "source /root/.bashrc && mri_convert /media/sub_ses_derivative_path_segment/SAMSEG_result/posteriors/Lesions.mgz /media/sub_ses_derivative_path_segment/sub-{self.sub}_ses-{self.ses}_lesions.nii.gz"', shell=True).wait()
                            
                        except Exception as e:   
                            print(f'[ERROR] - {self.pipeline} | {e} while running Samseg for sub-{self.sub}_ses{self.ses}!')
                            self.end_run()
                            return
                    
                ## Binarizing the lesion probability  mask    
                # Pre check
                ## check if files exist
                if not pexists(pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz')):
                    file = pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz')
                    print(f'[ERROR] - {self.pipeline} | FileNotFound: File "{file}" not Found !')
                    self.end_run()
                    return
                
                try:                
                    # Actions
                    print(f'Binarizing lesion probability mask for sub-{self.sub} ses-{self.ses}...')
                   
                    threshold = 0.5
                    image = nib.load(pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions.nii.gz'))
                    lesions = image.get_fdata()
                    lesions[lesions >= threshold] = 1
                    lesions[lesions < threshold] = 0
                
                    lesions_nifti = nib.Nifti1Image(lesions, affine=image.affine)
                    nib.save(lesions_nifti, pjoin(sub_ses_derivative_path_segment, f'sub-{self.sub}_ses-{self.ses}_lesions_binary.nii.gz'))
                    
                except Exception as e:
                    print(f'[ERROR] - {self.pipeline} | {e} while binarizing lesion probability mask for sub-{self.sub}_ses{self.ses}!')
                    self.end_run()
                    return
                
                print('End SAMSEG!')
        self.end_run()
                
    def end_run(self):
        self.in_progress.emit((self.pipeline, False))
        self.finished.emit()     
        
                       
