# YaMovesetOrganizer
This is a simple tool that allows copying/pasting moves from other movesets to create a new one.  The tool shows BAC entries and when pasting BAC entries, it will automatically create/overwrite EAN Animations and BDM entries.  

# Credits
* SK for the BAC Moveset Info file 

# Change Log
```
0.1.0 - Initial Release
0.1.1 - Bug fixes made CAM.EAN and BDM files optional to open (but fail if they are required by a BAC Entry), added more context into errors finding certain indexes if EAN/BDM files don’t match up with the BAC file.
0.1.2 - Fixed another bug with BDM copying
0.1.3 - Fixed an issue when copying to an Entry that doesn't have the same number of EAN/BDM Entries
0.1.4 - Fixed an issue that was caused by the last fix
0.1.5 - Added some missing BAC Entry names for the Stamina Breaks.
0.1.6 - Optimized EAN operations so saving is faster
0.1.7 - Updated some more BAC Entry names, added EAN Animation names showing what was replaced after pasting
0.2.0 - Improved pasting to cut down on duplicate animations, follow up paste dialog made to be more informative, Updated more BAC Entry names.
0.2.1 - Fixed bug with certain animations
0.2.2 - Another minor bug fix
0.2.3 - More bug fixes with BAC Entries that contain many animations
0.2.4 - More bug fixes
```
