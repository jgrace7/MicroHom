  [./elasticity_{{PHASE}}]
    type = ComputeElasticityTensor
    block = {{BLOCK}}
    fill_method = axisymmetric_rz
    C_ijkl = '{{C11}} {{C12}} {{C13}} {{C33}} {{C44}}'
  [../]

  [./eigen_{{PHASE}}]
    type             = ComputeEigenstrain
    block            = '{{BLOCK}}'
    eigen_base       =  '{{eig}}'
    prefactor        = 1
    eigenstrain_name = eigenstrain
  [../]

  [./stress_{{PHASE}}]
    type  = ComputeLinearElasticStress
    block = '{{BLOCK}}'
  [../]
