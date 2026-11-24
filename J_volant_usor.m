function J = J_volant_usor(P)
% J_VOLANT_USOR  Volantul „ușor”: arborele cotit (s12, cu masele din Fusion) + rotorul mașinii (s15).
J = echilibrare(P).J + isg_geometrie(P).J_rotor;
end
