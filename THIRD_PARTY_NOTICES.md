# Third Party Notices

## NeqSim (Non-Equilibrium Simulator)

Thermodynamic and process engineering toolkit by Equinor / NTNU.
Used in `natural_gas_main/models/neqsim_calculator.py` for 15+ EOS models.

https://github.com/equinor/neqsim
https://github.com/equinor/neqsim-python

Copyright (c) 2025 Equinor ASA

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---

## mkamyab/zfactor

The Standing-Katz ANN10, ANN5 and Dranchuk-Abou-Kassem Z-factor fallback implementation in
`natural_gas_main/models/z_factor.py` adapts coefficients and formulas from:

https://github.com/mkamyab/zfactor

Copyright (c) 2015 Mohammadreza Kamyab, and Jorge H.B. Sampaio

Licensed under the MIT License.

Reference paper:

Kamyab, M.; Sampaio Jr., J. H. B.; Qanbari, F.; Eustes III, A. W.
"Using artificial neural networks to estimate the Z-Factor for natural hydrocarbon gases",
Journal of Petroleum Science and Engineering, 2010, 73, 248-257.

---

## fpdf2

PDF generation library used via `natural_gas_main/utils/report_generator.py`.

https://github.com/PyFPDF/fpdf2

Copyright (c) 2021-2025 Olivier PLATHEY and contributors

Licensed under the GNU Lesser General Public License v3 or later (LGPLv3+).

**LGPL Source Code Notice:**
This application statically links fpdf2 (LGPL-licensed). You are entitled to
receive the source code and any modifications of fpdf2 used in this application.
Source code for this application is available at:
https://github.com/anomalyco/Natural-Gas-Prop-Main

To obtain the complete corresponding source code for the LGPL-licensed components,
please contact the application author or visit the fpdf2 repository at:
https://github.com/PyFPDF/fpdf2
