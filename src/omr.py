import subprocess
import os 
from pathlib import Path
import shutil
from lxml import etree

class OMR:
    """
    This class will perform Optical Music Recognition on a PDF using Audiveris, then
    output to MusicXML file, while cleaning up extraneous files and folders. 
    """
    def __init__(self, input_pdf_path: str, output_path: str):
        self.input_pdf_path = input_pdf_path
        self.output_path = output_path
        
    def run_audiveris(self) -> None:
        """
        Run Audiveris CLI to convert a PDF into a MusicXML file.
        """
        script_path = "../audiveris-cli.sh"
        cmd = [
            script_path, 
            "-batch", 
            "-export", 
            "-output", self.output_path,
            self.input_pdf_path
        ]
        try:
            subprocess.run(cmd, check=True)
            print("Audiveris processing completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Audiveris failed with exit code {e.returncode}")

    def unzip_mxls(self) -> None:
        """
        Unzip the resulting .mxl file(s)
        """
        output_path = Path(self.output_path)
        mxl_files = output_path.glob("*.mxl")

        print("--- Unzip .mxl file(s) --- ")
        
        for mxl_file in mxl_files:
            try:
                subprocess.run(["unzip", "-o", mxl_file, "-d", str(output_path)], check=True)
                print(f"{mxl_file} unzipped successfully")
            except subprocess.CalledProcessError as e:
                print(f"unzip failed with exit code {e.returncode}")
    
    def check_for_xml_file(self) -> bool:
        directory = Path(self.output_path)

        return any(directory.glob("*.xml"))

    def delete_files_metafolder(self) -> None:
        """
        Delete non .xml files and 'META-INF' folder, keep log file  
        (Produced by Audioveris and The unzipping of the .mxl file(s))
        """
        directory = Path(self.output_path)
        extensions = {'.mxl', '.omr'}

        print("--- Delete non .xml files and folders, keep log --- ")

        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix in extensions:
                print(f"Deleting {file_path}")
                os.remove(file_path)
                
        dir_to_delete = directory / 'META-INF'
        if dir_to_delete.exists() and dir_to_delete.is_dir():
            print("Deleting META-INF directory")
            shutil.rmtree(dir_to_delete)

        if not self.check_for_xml_file():
            print("OMR FAILED: No .xml file produced. Check Logs.")
        else:
            print("OMR Succeeded!")

    def strip_chords(self) -> None:
        """
        If MusicXML file has chords above staff, remove them
        ie, it strips <harmony> tags. These get played in playback. 
        """
        original_file = Path(self.input_pdf_path)
        base_name = original_file.stem
        xml_to_process = Path(self.output_path) / f"{base_name}.xml"

        if not xml_to_process.exists(): 
            print(f'File not found: {xml_to_process}') 
            return 

        try:
            tree = etree.parse(xml_to_process)
        except etree.XMLSyntaxError as e:
            print(f"Failed to parse XML: {e}")
            return

        root = tree.getroot()
        tag_to_remove = 'harmony'
        for elem in root.xpath('.//' + tag_to_remove):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

        tree.write(
            xml_to_process,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        )

        print('Chords Stripped.')




            
