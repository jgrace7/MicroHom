  [./elasticity_{{PHASE}}]
    type = ComputeElasticityTensor
    block = {{BLOCK}}
    fill_method = axisymmetric_rz
    C_ijkl = '{{C11}} {{C12}} {{C13}} {{C33}} {{C44}}'
  [../]
