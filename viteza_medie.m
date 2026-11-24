function w = viteza_medie(om)
% VITEZA_MEDIE  Viteza medie în timp (unghi parcurs / timp) a unei viteze
% eșantionate uniform pe unghi. Este turația pe care o arată un turometru.
% Media simplă a eșantioanelor ar fi media pe unghi, mai mare la fluctuații mari.
w = numel(om)/sum(1./om);
end
