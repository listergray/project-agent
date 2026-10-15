export interface FurnitureDef {
  id: string;
  name: string;
  category: string;
  icon: string;
  color: string;
  /** width x depth x height in cm */
  width: number;
  depth: number;
  height: number;
  /** If set, this is a 2D-only architectural symbol (not rendered in 3D) */
  symbol?: boolean;
}

export const furnitureCatalog: FurnitureDef[] = [
  // Living Room
  { id: 'sofa', name: '沙发', category: '客厅', icon: '🛋️', color: '#a78bfa', width: 200, depth: 90, height: 80 },
  { id: 'loveseat', name: '双人沙发', category: '客厅', icon: '🛋️', color: '#8b5cf6', width: 140, depth: 85, height: 80 },
  { id: 'chair', name: '扶手椅', category: '客厅', icon: '💺', color: '#c084fc', width: 80, depth: 80, height: 90 },
  { id: 'coffee_table', name: '茶几', category: '客厅', icon: '☕', color: '#92400e', width: 120, depth: 60, height: 45 },
  { id: 'tv_stand', name: '电视柜', category: '客厅', icon: '📺', color: '#475569', width: 150, depth: 45, height: 50 },
  { id: 'bookshelf', name: '书架', category: '客厅', icon: '📚', color: '#92400e', width: 80, depth: 30, height: 180 },
  { id: 'side_table', name: '边几', category: '客厅', icon: '🪑', color: '#a16207', width: 50, depth: 50, height: 55 },
  // Bedroom
  { id: 'bed_queen', name: '双人床', category: '卧室', icon: '🛏️', color: '#60a5fa', width: 200, depth: 150, height: 50 },
  { id: 'bed_twin', name: '单人床', category: '卧室', icon: '🛏️', color: '#93c5fd', width: 190, depth: 100, height: 50 },
  { id: 'nightstand', name: '床头柜', category: '卧室', icon: '🛏️', color: '#a16207', width: 50, depth: 40, height: 55 },
  { id: 'dresser', name: '斗柜', category: '卧室', icon: '🗄️', color: '#92400e', width: 120, depth: 50, height: 80 },
  { id: 'wardrobe', name: '衣柜', category: '卧室', icon: '🗄️', color: '#a16207', width: 120, depth: 60, height: 200 },
  // Kitchen
  { id: 'stove', name: '灶台', category: '厨房', icon: '🍳', color: '#f87171', width: 60, depth: 60, height: 85 },
  { id: 'fridge', name: '冰箱', category: '厨房', icon: '🧊', color: '#d1d5db', width: 70, depth: 70, height: 180 },
  { id: 'sink_k', name: '水槽', category: '厨房', icon: '🚰', color: '#94a3b8', width: 60, depth: 45, height: 85 },
  { id: 'counter', name: '橱柜', category: '厨房', icon: '🔲', color: '#78716c', width: 120, depth: 60, height: 85 },
  { id: 'dishwasher', name: '洗碗机', category: '厨房', icon: '🫧', color: '#cbd5e1', width: 60, depth: 60, height: 85 },
  { id: 'oven', name: '烤箱', category: '厨房', icon: '🔥', color: '#78716c', width: 60, depth: 60, height: 85 },
  // Bathroom
  { id: 'toilet', name: '马桶', category: '卫生间', icon: '🚽', color: '#e5e7eb', width: 40, depth: 65, height: 40 },
  { id: 'bathtub', name: '浴缸', category: '卫生间', icon: '🛁', color: '#93c5fd', width: 170, depth: 75, height: 60 },
  { id: 'shower', name: '淋浴', category: '卫生间', icon: '🚿', color: '#bae6fd', width: 90, depth: 90, height: 210 },
  { id: 'sink_b', name: '水槽', category: '卫生间', icon: '🪥', color: '#cbd5e1', width: 60, depth: 45, height: 85 },
  { id: 'washer_dryer', name: '洗衣机', category: '卫生间', icon: '👕', color: '#e2e8f0', width: 60, depth: 65, height: 85 },
  // Office
  { id: 'desk', name: '书桌', category: '书房', icon: '🖥️', color: '#34d399', width: 140, depth: 70, height: 75 },
  { id: 'office_chair', name: '办公椅', category: '书房', icon: '🪑', color: '#6b7280', width: 45, depth: 45, height: 90 },
  // Dining
  { id: 'dining_table', name: '餐桌', category: '餐厅', icon: '🍽️', color: '#f59e0b', width: 120, depth: 80, height: 75 },
  { id: 'dining_chair', name: '餐椅', category: '餐厅', icon: '🪑', color: '#d97706', width: 45, depth: 45, height: 90 },
  // Living Room extras
  { id: 'fireplace', name: '壁炉', category: '客厅', icon: '🔥', color: '#92400e', width: 120, depth: 40, height: 120 },
  { id: 'television', name: '电视', category: '客厅', icon: '📺', color: '#1e293b', width: 120, depth: 8, height: 70 },
  { id: 'storage', name: '储物柜', category: '客厅', icon: '🗄️', color: '#78716c', width: 100, depth: 50, height: 120 },
  { id: 'table', name: '桌子', category: '客厅', icon: '🪑', color: '#a16207', width: 100, depth: 60, height: 75 },
  // Decor
  { id: 'rug', name: '地毯', category: '装饰', icon: '🟫', color: '#c2956b', width: 200, depth: 300, height: 1 },
  { id: 'round_rug', name: '圆地毯', category: '装饰', icon: '⭕', color: '#b87d5e', width: 200, depth: 200, height: 1 },
  { id: 'runner_rug', name: '长条地毯', category: '装饰', icon: '🟫', color: '#a0694e', width: 80, depth: 250, height: 1 },
  { id: 'potted_plant', name: '盆栽', category: '装饰', icon: '🪴', color: '#4ade80', width: 40, depth: 40, height: 60 },
  { id: 'floor_plant', name: '落地植物', category: '装饰', icon: '🌿', color: '#22c55e', width: 50, depth: 50, height: 120 },
  { id: 'hanging_plant', name: '吊盆植物', category: '装饰', icon: '🌱', color: '#86efac', width: 30, depth: 30, height: 40 },
  { id: 'curtain', name: '窗帘', category: '装饰', icon: '🪟', color: '#e2c9a6', width: 120, depth: 10, height: 260 },
  { id: 'sheer_curtain', name: '纱帘', category: '装饰', icon: '🪟', color: '#f5f0e8', width: 120, depth: 10, height: 260 },
  { id: 'wall_art', name: '挂画', category: '装饰', icon: '🖼️', color: '#f59e0b', width: 80, depth: 5, height: 60 },
  { id: 'mirror', name: '镜子', category: '装饰', icon: '🪞', color: '#94a3b8', width: 60, depth: 5, height: 90 },
  { id: 'clock', name: '时钟', category: '装饰', icon: '🕐', color: '#1e293b', width: 30, depth: 5, height: 30 },
  // Lighting
  { id: 'ceiling_light', name: '吸顶灯', category: '照明', icon: '💡', color: '#fef08a', width: 40, depth: 40, height: 15 },
  { id: 'chandelier', name: '吊灯', category: '照明', icon: '✨', color: '#fcd34d', width: 60, depth: 60, height: 50 },
  { id: 'recessed_light', name: '筒灯', category: '照明', icon: '🔆', color: '#fef9c3', width: 15, depth: 15, height: 5 },
  { id: 'floor_lamp', name: '落地灯', category: '照明', icon: '🪔', color: '#e5e7eb', width: 40, depth: 40, height: 160 },
  { id: 'table_lamp', name: '台灯', category: '照明', icon: '💡', color: '#fde68a', width: 25, depth: 25, height: 45 },
  { id: 'wall_sconce', name: '壁灯', category: '照明', icon: '🔅', color: '#fef3c7', width: 15, depth: 10, height: 20 },
  { id: 'pendant_light', name: '吊灯', category: '照明', icon: '💡', color: '#fbbf24', width: 30, depth: 30, height: 30 },

  // Outdoor Furniture
  { id: 'patio_table', name: '户外桌', category: '户外家具', icon: '🪑', color: '#92400e', width: 120, depth: 120, height: 75 },
  { id: 'patio_chair', name: '户外椅', category: '户外家具', icon: '🪑', color: '#a16207', width: 55, depth: 55, height: 85 },
  { id: 'bench_outdoor', name: '长椅', category: '户外家具', icon: '🪑', color: '#78716c', width: 150, depth: 50, height: 80 },
  { id: 'lounger', name: '躺椅', category: '户外家具', icon: '🛏️', color: '#d97706', width: 70, depth: 190, height: 35 },
  { id: 'umbrella', name: '遮阳伞', category: '户外家具', icon: '☂️', color: '#ef4444', width: 200, depth: 200, height: 230 },
  { id: 'bbq_grill', name: '烧烤架', category: '户外家具', icon: '🔥', color: '#374151', width: 80, depth: 50, height: 100 },
  { id: 'fire_pit', name: '火坑', category: '户外家具', icon: '🔥', color: '#78716c', width: 90, depth: 90, height: 40 },
  { id: 'campfire', name: '营火', category: '户外家具', icon: '🏕️', color: '#b45309', width: 60, depth: 60, height: 30 },
  { id: 'picnic_table', name: '野餐桌', category: '户外家具', icon: '🍽️', color: '#92400e', width: 180, depth: 140, height: 75 },
  { id: 'tent', name: '帐篷', category: '户外家具', icon: '⛺', color: '#d4a373', width: 200, depth: 200, height: 140 },
  { id: 'outdoor_sign', name: '指示牌', category: '户外家具', icon: '🪧', color: '#92400e', width: 40, depth: 10, height: 120 },
  { id: 'outdoor_pot_large', name: '大花盆', category: '户外家具', icon: '🏺', color: '#b45309', width: 40, depth: 40, height: 35 },
  { id: 'outdoor_pot_small', name: '小花盆', category: '户外家具', icon: '🏺', color: '#b45309', width: 25, depth: 25, height: 25 },

  // Landscaping — Trees
  { id: 'tree_oak', name: '橡树', category: '景观', icon: '🌳', color: '#166534', width: 300, depth: 300, height: 500 },
  { id: 'tree_default', name: '落叶树', category: '景观', icon: '🌳', color: '#15803d', width: 250, depth: 250, height: 450 },
  { id: 'tree_detailed', name: '细节树', category: '景观', icon: '🌳', color: '#14532d', width: 280, depth: 280, height: 480 },
  { id: 'tree_pine', name: '松树', category: '景观', icon: '🌲', color: '#065f46', width: 150, depth: 150, height: 500 },
  { id: 'tree_pine_tall', name: '高松', category: '景观', icon: '🌲', color: '#064e3b', width: 120, depth: 120, height: 600 },
  { id: 'tree_palm', name: '棕榈', category: '景观', icon: '🌴', color: '#16a34a', width: 200, depth: 200, height: 500 },
  { id: 'tree_palm_bend', name: '弯棕榈', category: '景观', icon: '🌴', color: '#22c55e', width: 200, depth: 200, height: 450 },
  { id: 'tree_palm_tall', name: '高棕榈', category: '景观', icon: '🌴', color: '#4ade80', width: 150, depth: 150, height: 600 },
  { id: 'tree_fat', name: '阔树', category: '景观', icon: '🌳', color: '#15803d', width: 350, depth: 350, height: 400 },
  { id: 'tree_simple', name: '简树', category: '景观', icon: '🌳', color: '#22c55e', width: 200, depth: 200, height: 350 },
  { id: 'tree_thin', name: '细树', category: '景观', icon: '🌳', color: '#166534', width: 100, depth: 100, height: 450 },
  { id: 'tree_tall', name: '高树', category: '景观', icon: '🌳', color: '#14532d', width: 200, depth: 200, height: 550 },
  { id: 'tree_cone', name: '锥形树', category: '景观', icon: '🌲', color: '#065f46', width: 150, depth: 150, height: 400 },
  { id: 'tree_blocky', name: '方块树', category: '景观', icon: '🌳', color: '#15803d', width: 200, depth: 200, height: 400 },
  { id: 'tree_small', name: '小树', category: '景观', icon: '🌳', color: '#4ade80', width: 120, depth: 120, height: 250 },

  // Landscaping — Bushes & Plants
  { id: 'bush', name: '灌木', category: '景观', icon: '🌿', color: '#22c55e', width: 80, depth: 80, height: 60 },
  { id: 'bush_detailed', name: '细节灌木', category: '景观', icon: '🌿', color: '#16a34a', width: 90, depth: 90, height: 70 },
  { id: 'bush_large', name: '大灌木', category: '景观', icon: '🌿', color: '#15803d', width: 120, depth: 120, height: 90 },
  { id: 'bush_large_triangle', name: '大三角灌木', category: '景观', icon: '🌿', color: '#166534', width: 120, depth: 120, height: 100 },
  { id: 'bush_small', name: '小灌木', category: '景观', icon: '🌿', color: '#4ade80', width: 50, depth: 50, height: 40 },
  { id: 'bush_triangle', name: '三角灌木', category: '景观', icon: '🌿', color: '#22c55e', width: 80, depth: 80, height: 80 },
  { id: 'hedge_row', name: '绿篱', category: '景观', icon: '🌿', color: '#166534', width: 200, depth: 60, height: 120 },
  { id: 'cactus_short', name: '矮仙人掌', category: '景观', icon: '🌵', color: '#4d7c0f', width: 30, depth: 30, height: 60 },
  { id: 'cactus_tall', name: '高仙人掌', category: '景观', icon: '🌵', color: '#365314', width: 30, depth: 30, height: 120 },
  { id: 'hanging_moss', name: '垂苔', category: '景观', icon: '🌿', color: '#86efac', width: 40, depth: 40, height: 80 },

  // Landscaping — Flowers
  { id: 'flower_purple', name: '紫花', category: '景观', icon: '🌸', color: '#a855f7', width: 20, depth: 20, height: 30 },
  { id: 'flower_red', name: '红花', category: '景观', icon: '🌹', color: '#ef4444', width: 20, depth: 20, height: 30 },
  { id: 'flower_yellow', name: '黄花', category: '景观', icon: '🌻', color: '#eab308', width: 20, depth: 20, height: 30 },
  { id: 'flower_purple_b', name: '紫花 B', category: '景观', icon: '🌸', color: '#c084fc', width: 25, depth: 25, height: 35 },
  { id: 'flower_red_b', name: '红花 B', category: '景观', icon: '🌹', color: '#f87171', width: 25, depth: 25, height: 35 },
  { id: 'flower_yellow_b', name: '黄花 B', category: '景观', icon: '🌻', color: '#facc15', width: 25, depth: 25, height: 35 },
  { id: 'flower_bed', name: '花床', category: '景观', icon: '🌺', color: '#f472b6', width: 100, depth: 40, height: 20 },
  { id: 'lily', name: '睡莲', category: '景观', icon: '🪷', color: '#86efac', width: 30, depth: 30, height: 5 },

  // Landscaping — Grass
  { id: 'grass_tuft', name: '草簇', category: '景观', icon: '🌾', color: '#84cc16', width: 30, depth: 30, height: 15 },
  { id: 'grass_large', name: '大草', category: '景观', icon: '🌾', color: '#65a30d', width: 40, depth: 40, height: 25 },
  { id: 'grass_leafs', name: '草叶', category: '景观', icon: '🌾', color: '#4d7c0f', width: 30, depth: 30, height: 20 },
  { id: 'grass_leafs_large', name: '大草叶', category: '景观', icon: '🌾', color: '#365314', width: 40, depth: 40, height: 30 },

  // Landscaping — Rocks & Stones
  { id: 'rock_large', name: '大岩石', category: '景观', icon: '🪨', color: '#78716c', width: 100, depth: 80, height: 60 },
  { id: 'rock_large_b', name: '大岩石 B', category: '景观', icon: '🪨', color: '#6b7280', width: 90, depth: 70, height: 55 },
  { id: 'rock_tall', name: '高岩石', category: '景观', icon: '🪨', color: '#57534e', width: 60, depth: 50, height: 100 },
  { id: 'rock_small', name: '小岩石', category: '景观', icon: '🪨', color: '#a8a29e', width: 30, depth: 25, height: 20 },
  { id: 'rock_small_b', name: '小岩石 B', category: '景观', icon: '🪨', color: '#d6d3d1', width: 25, depth: 20, height: 18 },
  { id: 'stone_large', name: '大石', category: '景观', icon: '🪨', color: '#9ca3af', width: 80, depth: 60, height: 50 },
  { id: 'stone_tall', name: '高石', category: '景观', icon: '🪨', color: '#6b7280', width: 50, depth: 40, height: 90 },
  { id: 'boulder', name: '巨石', category: '景观', icon: '🪨', color: '#57534e', width: 150, depth: 120, height: 100 },

  // Landscaping — Misc
  { id: 'mushroom_red', name: '红蘑菇', category: '景观', icon: '🍄', color: '#dc2626', width: 20, depth: 20, height: 25 },
  { id: 'mushroom_group', name: '蘑菇群', category: '景观', icon: '🍄', color: '#ef4444', width: 30, depth: 30, height: 20 },
  { id: 'mushroom_tan', name: '褐蘑菇', category: '景观', icon: '🍄', color: '#d4a373', width: 20, depth: 20, height: 25 },
  { id: 'log_single', name: '原木', category: '景观', icon: '🪵', color: '#92400e', width: 30, depth: 100, height: 30 },
  { id: 'log_large', name: '大原木', category: '景观', icon: '🪵', color: '#78350f', width: 40, depth: 120, height: 40 },
  { id: 'log_stack', name: '柴堆', category: '景观', icon: '🪵', color: '#92400e', width: 80, depth: 60, height: 50 },
  { id: 'stump_old', name: '老树桩', category: '景观', icon: '🪵', color: '#78350f', width: 40, depth: 40, height: 30 },
  { id: 'stump_round', name: '圆树桩', category: '景观', icon: '🪵', color: '#92400e', width: 35, depth: 35, height: 25 },
  { id: 'corn', name: '玉米秆', category: '景观', icon: '🌽', color: '#84cc16', width: 30, depth: 30, height: 120 },
  { id: 'pumpkin', name: '南瓜', category: '景观', icon: '🎃', color: '#ea580c', width: 30, depth: 30, height: 25 },
  { id: 'statue_column', name: '柱像', category: '景观', icon: '🏛️', color: '#d1d5db', width: 30, depth: 30, height: 200 },
  { id: 'obelisk', name: '方尖碑', category: '景观', icon: '🏛️', color: '#9ca3af', width: 40, depth: 40, height: 250 },

  // Fencing
  { id: 'fence_simple', name: '简易围栏', category: '围栏', icon: '🏗️', color: '#92400e', width: 200, depth: 10, height: 100 },
  { id: 'fence_planks', name: '板条围栏', category: '围栏', icon: '🏗️', color: '#a16207', width: 200, depth: 10, height: 120 },
  { id: 'fence_gate', name: '围栏门', category: '围栏', icon: '🚪', color: '#78350f', width: 100, depth: 10, height: 100 },
  { id: 'fence_corner', name: '围栏角', category: '围栏', icon: '🏗️', color: '#92400e', width: 100, depth: 100, height: 100 },
  { id: 'picket_fence', name: '尖桩围栏', category: '围栏', icon: '🏗️', color: '#fef3c7', width: 200, depth: 10, height: 90 },
  { id: 'metal_fence', name: '金属围栏', category: '围栏', icon: '🏗️', color: '#374151', width: 200, depth: 10, height: 120 },

  // Structures
  { id: 'pergola', name: '花架', category: '构筑物', icon: '🏗️', color: '#92400e', width: 300, depth: 300, height: 250 },
  { id: 'deck_patio', name: '露台', category: '构筑物', icon: '🏗️', color: '#a16207', width: 400, depth: 300, height: 15 },
  { id: 'raised_garden_bed', name: '抬高花床', category: '构筑物', icon: '🌱', color: '#78350f', width: 120, depth: 60, height: 40 },
  { id: 'shed', name: '花园小屋', category: '构筑物', icon: '🏠', color: '#78716c', width: 200, depth: 250, height: 230 },
  { id: 'gazebo', name: '凉亭', category: '构筑物', icon: '🏗️', color: '#e5e7eb', width: 300, depth: 300, height: 280 },
  { id: 'planter_box', name: '花箱', category: '构筑物', icon: '🌱', color: '#92400e', width: 80, depth: 30, height: 30 },
  { id: 'raised_bed', name: '抬高花床', category: '构筑物', icon: '🌱', color: '#7B5B3A', width: 180, depth: 90, height: 40 },

  // Pool & Spa
  { id: 'pool_rectangular', name: '矩形泳池', category: '泳池', icon: '🏊', color: '#0ea5e9', width: 500, depth: 300, height: 15 },
  { id: 'pool_round', name: '圆形泳池', category: '泳池', icon: '🏊', color: '#0ea5e9', width: 300, depth: 300, height: 15 },
  { id: 'pool_lshaped', name: 'L 形泳池', category: '泳池', icon: '🏊', color: '#0891b2', width: 600, depth: 400, height: 15 },
  { id: 'pool_kidney', name: '肾形泳池', category: '泳池', icon: '🏊', color: '#06b6d4', width: 500, depth: 280, height: 15 },
  { id: 'hot_tub', name: '按摩浴缸', category: '泳池', icon: '♨️', color: '#0284c7', width: 200, depth: 200, height: 80 },
  { id: 'pool_ladder', name: '泳池梯', category: '泳池', icon: '🪜', color: '#94a3b8', width: 50, depth: 30, height: 100 },
  { id: 'diving_board', name: '跳板', category: '泳池', icon: '🏊', color: '#e2e8f0', width: 50, depth: 200, height: 80 },
  { id: 'pool_lounge', name: '泳池躺椅', category: '泳池', icon: '🛏️', color: '#f8fafc', width: 70, depth: 190, height: 35 },

  // Garage
  { id: 'car_sedan', name: '轿车', category: '车库', icon: '🚗', color: '#475569', width: 180, depth: 450, height: 150 },
  { id: 'car_suv', name: 'SUV', category: '车库', icon: '🚙', color: '#334155', width: 190, depth: 480, height: 170 },
  { id: 'garage_door_single', name: '车库门（单）', category: '车库', icon: '🚪', color: '#9ca3af', width: 280, depth: 10, height: 220 },
  { id: 'garage_door_double', name: '车库门（双）', category: '车库', icon: '🚪', color: '#9ca3af', width: 500, depth: 10, height: 220 },
  { id: 'workbench', name: '工作台', category: '车库', icon: '🔧', color: '#78716c', width: 180, depth: 60, height: 90 },
  { id: 'tool_cabinet', name: '工具柜', category: '车库', icon: '🧰', color: '#dc2626', width: 70, depth: 45, height: 140 },
  { id: 'bike', name: '自行车', category: '车库', icon: '🚲', color: '#374151', width: 60, depth: 170, height: 110 },
  { id: 'motorcycle', name: '摩托车', category: '车库', icon: '🏍️', color: '#1e293b', width: 80, depth: 210, height: 110 },

  // Paths & Lawns
  { id: 'lawn_rect', name: '草坪（矩形）', category: '路径与草坪', icon: '🟩', color: '#22c55e', width: 400, depth: 300, height: 3 },
  { id: 'lawn_square', name: '草坪（方形）', category: '路径与草坪', icon: '🟩', color: '#22c55e', width: 300, depth: 300, height: 3 },
  { id: 'lawn_large', name: '草坪（大）', category: '路径与草坪', icon: '🟩', color: '#16a34a', width: 600, depth: 400, height: 3 },
  { id: 'path_straight', name: '直道', category: '路径与草坪', icon: '🟫', color: '#a8a29e', width: 100, depth: 300, height: 3 },
  { id: 'path_wide', name: '宽道', category: '路径与草坪', icon: '🟫', color: '#a8a29e', width: 150, depth: 300, height: 3 },
  { id: 'patio_stone', name: '石露台', category: '路径与草坪', icon: '🪨', color: '#d6d3d1', width: 300, depth: 300, height: 5 },
  { id: 'gravel_area', name: '砾石区', category: '路径与草坪', icon: '⬜', color: '#e7e5e4', width: 200, depth: 200, height: 3 },
  { id: 'stepping_stones', name: '汀步', category: '路径与草坪', icon: '🪨', color: '#a8a29e', width: 60, depth: 300, height: 3 },
  { id: 'driveway', name: '车道', category: '路径与草坪', icon: '🟫', color: '#78716c', width: 300, depth: 600, height: 3 },
  { id: 'sandbox', name: '沙坑', category: '路径与草坪', icon: '🏖️', color: '#fbbf24', width: 200, depth: 200, height: 20 },

  // Outdoor Lighting
  { id: 'lamp_post', name: '路灯', category: '户外照明', icon: '🔦', color: '#1e293b', width: 30, depth: 30, height: 300 },
  { id: 'lamp_post_double', name: '双头路灯', category: '户外照明', icon: '🔦', color: '#1e293b', width: 60, depth: 30, height: 300 },
  { id: 'bollard_light', name: '地灯', category: '户外照明', icon: '💡', color: '#374151', width: 15, depth: 15, height: 80 },
  { id: 'wall_sconce_outdoor', name: '壁灯', category: '户外照明', icon: '💡', color: '#374151', width: 20, depth: 15, height: 30 },
  { id: 'spot_light_outdoor', name: '射灯', category: '户外照明', icon: '🔆', color: '#1e293b', width: 15, depth: 15, height: 25 },
  { id: 'string_lights', name: '串灯', category: '户外照明', icon: '✨', color: '#fbbf24', width: 300, depth: 10, height: 250 },
  { id: 'solar_path_light', name: '太阳能路径灯', category: '户外照明', icon: '☀️', color: '#374151', width: 12, depth: 12, height: 40 },
  { id: 'flood_light', name: '泛光灯', category: '户外照明', icon: '🔦', color: '#1e293b', width: 25, depth: 20, height: 30 },

  // Garden Structures
  { id: 'greenhouse', name: '温室', category: '花园构筑物', icon: '🏡', color: '#86efac', width: 300, depth: 400, height: 250 },
  { id: 'greenhouse_small', name: '小温室', category: '花园构筑物', icon: '🏡', color: '#86efac', width: 200, depth: 250, height: 200 },
  { id: 'trellis', name: '格架', category: '花园构筑物', icon: '🌿', color: '#92400e', width: 150, depth: 10, height: 200 },
  { id: 'arbor', name: '花园拱门', category: '花园构筑物', icon: '🌿', color: '#92400e', width: 150, depth: 60, height: 230 },
  { id: 'compost_bin', name: '堆肥箱', category: '花园构筑物', icon: '🗑️', color: '#422006', width: 80, depth: 80, height: 90 },
  { id: 'rain_barrel', name: '雨水桶', category: '花园构筑物', icon: '🛢️', color: '#3b82f6', width: 60, depth: 60, height: 90 },
  { id: 'bird_bath', name: '鸟浴盆', category: '花园构筑物', icon: '🐦', color: '#d6d3d1', width: 50, depth: 50, height: 80 },
  { id: 'fountain', name: '喷泉', category: '花园构筑物', icon: '⛲', color: '#94a3b8', width: 120, depth: 120, height: 150 },
  { id: 'statue', name: '花园雕塑', category: '花园构筑物', icon: '🗿', color: '#d6d3d1', width: 40, depth: 40, height: 120 },
  { id: 'mailbox', name: '邮箱', category: '花园构筑物', icon: '📫', color: '#1e293b', width: 30, depth: 20, height: 110 },

  // Electrical Symbols (2D only)
  { id: 'sym_outlet', name: '电源插座', category: '电气', icon: '🔌', color: '#2563eb', width: 15, depth: 15, height: 0, symbol: true },
  { id: 'sym_switch', name: '开关', category: '电气', icon: '🔘', color: '#2563eb', width: 15, depth: 15, height: 0, symbol: true },
  { id: 'sym_ceiling_light', name: '吸顶灯', category: '电气', icon: '💡', color: '#eab308', width: 20, depth: 20, height: 0, symbol: true },
  { id: 'sym_recessed_light', name: '筒灯', category: '电气', icon: '🔆', color: '#eab308', width: 15, depth: 15, height: 0, symbol: true },
  { id: 'sym_pendant', name: '吊灯', category: '电气', icon: '💡', color: '#eab308', width: 18, depth: 18, height: 0, symbol: true },
  { id: 'sym_ceiling_fan', name: '吊扇', category: '电气', icon: '🌀', color: '#2563eb', width: 25, depth: 25, height: 0, symbol: true },
  { id: 'sym_junction', name: '接线盒', category: '电气', icon: '⬜', color: '#2563eb', width: 12, depth: 12, height: 0, symbol: true },
  { id: 'sym_smoke', name: '烟感', category: '电气', icon: '🔔', color: '#dc2626', width: 15, depth: 15, height: 0, symbol: true },

  // Plumbing Symbols (2D only)
  { id: 'sym_water_supply', name: '给水点', category: '给排水', icon: '💧', color: '#0ea5e9', width: 15, depth: 15, height: 0, symbol: true },
  { id: 'sym_drain', name: '排水点', category: '给排水', icon: '⬇️', color: '#0ea5e9', width: 15, depth: 15, height: 0, symbol: true },
  { id: 'sym_water_heater', name: '热水器', category: '给排水', icon: '🔥', color: '#ef4444', width: 20, depth: 20, height: 0, symbol: true },
  { id: 'sym_washer_hookup', name: '洗衣机接口', category: '给排水', icon: '🧺', color: '#0ea5e9', width: 15, depth: 15, height: 0, symbol: true },
  { id: 'sym_gas_line', name: '燃气管', category: '给排水', icon: '⛽', color: '#f59e0b', width: 15, depth: 15, height: 0, symbol: true },
];

export function getCatalogItem(id: string): FurnitureDef | undefined {
  return furnitureCatalog.find(f => f.id === id);
}

export const furnitureCategories = [...new Set(furnitureCatalog.map(f => f.category))];
