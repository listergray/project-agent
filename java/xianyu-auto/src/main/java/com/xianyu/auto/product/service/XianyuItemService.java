package com.xianyu.auto.product.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.product.entity.Product;
import com.xianyu.auto.xianyu.auth.CookieManager;
import com.xianyu.auto.xianyu.client.XianyuApiClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 闲鱼商品同步 / 上下架 / 发布 / 搬家
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class XianyuItemService {

    private final ProductService productService;
    private final AccountService accountService;
    private final CookieManager cookieManager;
    private final XianyuApiClient apiClient;

    public Map<String, Object> syncFromXianyu(Long accountId) {
        Account account = requireAccount(accountId);
        String cookie = requireCookie(accountId);
        // 同步前先刷 _m_h5_tk，避免 TOKEN_EXOIRED
        String refreshed = apiClient.refreshMh5Tk(cookie);
        if (!refreshed.equals(cookie)) {
            accountService.updateCookieQuiet(accountId, refreshed);
            cookie = refreshed;
            log.info("同步前已刷新 _m_h5_tk: accountId={}", accountId);
        }
        String userId = account.getUserId();
        if (!StringUtils.hasText(userId)) {
            userId = cookieManager.getUnb(accountId);
        }
        if (!StringUtils.hasText(userId)) {
            throw new BusinessException("账号缺少 userId(unb)");
        }

        int page = 1;
        int upserted = 0;
        int errors = 0;
        String nextPageModel = null;
        String nextPageNum = null;
        while (page <= 50) {
            JsonNode resp;
            try {
                XianyuApiClient.CookieBoundResult bound =
                        apiClient.listSellerItemsBound(cookie, userId, page, 20, nextPageModel, nextPageNum);
                if (bound.cookie() != null && !bound.cookie().equals(cookie)) {
                    accountService.updateCookieQuiet(accountId, bound.cookie());
                    cookie = bound.cookie();
                }
                resp = bound.result();
            } catch (Exception e) {
                log.warn("同步商品列表失败 page={}: {}", page, e.getMessage());
                errors++;
                break;
            }
            if (!apiClient.isApiSuccess(resp)) {
                String ret = resp.path("ret").toString();
                if (ret.contains("TOKEN_EXOIRED") || ret.contains("TOKEN_EXPIRED")
                        || ret.contains("SESSION_EXPIRED")) {
                    throw new BusinessException("登录令牌已失效，请重新扫码/录入 Cookie 后再同步: " + resp.path("ret"));
                }
                throw new BusinessException("同步商品失败: " + resp.path("ret"));
            }
            List<JsonNode> items = extractItemNodes(resp);
            if (items.isEmpty()) {
                break;
            }
            for (JsonNode item : items) {
                try {
                    Product saved = upsertProductFromNode(accountId, item);
                    // 列表接口不含库存/完整描述，用详情补全价格、库存、上下架
                    if (saved != null && StringUtils.hasText(saved.getXianyuItemId())) {
                        try {
                            JsonNode detail = apiClient.itemDetail(cookie, saved.getXianyuItemId());
                            if (apiClient.isApiSuccess(detail)) {
                                applyDetailToProduct(saved, detail);
                                saved.setLastSyncedAt(DateUtils.nowMillis());
                                saved.setSyncStatus(Product.SYNC_OK);
                                saved.setUpdatedAt(DateUtils.nowMillis());
                                productService.updateById(saved);
                            }
                        } catch (Exception de) {
                            log.debug("详情补全跳过 itemId={}: {}", saved.getXianyuItemId(), de.getMessage());
                        }
                    }
                    upserted++;
                    Thread.sleep(200 + (long) (Math.random() * 400));
                } catch (Exception e) {
                    errors++;
                    log.warn("同步单品失败: {}", e.getMessage());
                }
            }
            JsonNode data = resp.path("data");
            JsonNode nextPageNode = data.path("nextPage");
            boolean hasNext = nextPageNode.isMissingNode() || nextPageNode.isNull()
                    ? items.size() >= 20
                    : nextPageNode.asBoolean(false);
            nextPageModel = text(data, "nextPageModel");
            nextPageNum = text(data, "nextPageNum");
            if (!hasNext) {
                break;
            }
            page++;
            try {
                Thread.sleep(500 + (long) (Math.random() * 800));
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        Map<String, Object> result = new HashMap<>();
        result.put("upserted", upserted);
        result.put("errors", errors);
        result.put("pages", page);
        return result;
    }

    /**
     * 新建本地商品并发布到闲鱼。成功后回写 xianyuItemId / 在售状态。
     */
    public Product publishNew(Long accountId, Product draft) {
        Account account = requireAccount(accountId);
        String cookie = requireCookie(accountId);
        if (draft == null) {
            throw new BusinessException("商品信息不能为空");
        }
        String title = StringUtils.hasText(draft.getTitle()) ? draft.getTitle() : draft.getName();
        if (!StringUtils.hasText(title)) {
            throw new BusinessException("商品标题不能为空");
        }
        if (draft.getPrice() == null || draft.getPrice().compareTo(BigDecimal.ZERO) < 0) {
            throw new BusinessException("商品价格无效");
        }

        long now = DateUtils.nowMillis();
        Product product = new Product();
        product.setAccountId(accountId);
        product.setName(title.length() > 200 ? title.substring(0, 200) : title);
        product.setTitle(title);
        product.setDescription(draft.getDescription());
        product.setPrice(draft.getPrice());
        product.setOriginalPrice(draft.getOriginalPrice());
        product.setStockQty(draft.getStockQty() != null ? draft.getStockQty() : 9999);
        product.setImagesJson(draft.getImagesJson());
        product.setCategoryId(draft.getCategoryId());
        product.setProvince(draft.getProvince());
        product.setCity(draft.getCity());
        product.setDeliveryContent(draft.getDeliveryContent());
        product.setAutoDelivery(draft.getAutoDelivery() != null ? draft.getAutoDelivery() : 1);
        product.setDefaultInventoryId(draft.getDefaultInventoryId());
        product.setShelfStatus(Product.SHELF_OFF);
        product.setSyncStatus(Product.SYNC_LOCAL);
        product.setStatus(Product.STATUS_ENABLED);
        product.setCreatedAt(now);
        product.setUpdatedAt(now);
        productService.save(product);

        if (!StringUtils.hasText(product.getCategoryId())
                && !isVideoServiceTitle(title)
                && !isWebsiteServiceTitle(title)) {
            product.setCategoryId("50023914");
            productService.updateById(product);
        }
        return publishPrepared(accountId, cookie, product);
    }

    /** 对已有本地草稿重新调用闲鱼发布（无 xianyuItemId 时） */
    public Product republish(Long accountId, Long productId) {
        requireAccount(accountId);
        String cookie = requireCookie(accountId);
        Product product = productService.getById(productId);
        if (product == null) {
            throw new BusinessException("商品不存在");
        }
        if (!accountId.equals(product.getAccountId())) {
            throw new BusinessException("商品不属于该账号");
        }
        if (StringUtils.hasText(product.getXianyuItemId())) {
            throw new BusinessException("商品已发布过闲鱼，请勿重复发布: " + product.getXianyuItemId());
        }
        return publishPrepared(accountId, cookie, product);
    }

    private Product publishPrepared(Long accountId, String cookie, Product product) {
        List<Map<String, Object>> imageDos = preparePublishImages(cookie, product);
        Map<String, Object> publishData = buildFullPublishPayload(cookie, product, imageDos);
        JsonNode pubResp = apiClient.publishItem(cookie, publishData);
        if (!apiClient.isApiSuccess(pubResp)) {
            product.setSyncStatus(Product.SYNC_ERROR);
            product.setUpdatedAt(DateUtils.nowMillis());
            productService.updateById(product);
            throw new BusinessException("发布失败: " + pubResp.path("ret") + " body=" + pubResp);
        }
        String newItemId = extractPublishedItemId(pubResp);
        if (!StringUtils.hasText(newItemId)) {
            throw new BusinessException("发布成功但未返回 itemId: " + pubResp);
        }
        product.setXianyuItemId(newItemId);
        product.setShelfStatus(Product.SHELF_ON_SALE);
        product.setSyncStatus(Product.SYNC_OK);
        product.setLastSyncedAt(DateUtils.nowMillis());
        product.setUpdatedAt(DateUtils.nowMillis());
        productService.updateById(product);
        log.info("发布成功 accountId={} productId={} itemId={} title={}",
                accountId, product.getId(), newItemId, product.getTitle());
        return product;
    }

    /** 已上架商品：按本地标题/描述重新提交闲鱼编辑 */
    public Product updateLiveCopy(Long accountId, Long productId) {
        requireAccount(accountId);
        String cookie = requireCookie(accountId);
        Product product = productService.getById(productId);
        if (product == null) {
            throw new BusinessException("商品不存在");
        }
        if (!StringUtils.hasText(product.getXianyuItemId())) {
            throw new BusinessException("商品尚未发布到闲鱼");
        }
        List<Map<String, Object>> imageDos = preparePublishImages(cookie, product);
        Map<String, Object> payload = buildFullPublishPayload(cookie, product, imageDos);
        payload.put("itemId", product.getXianyuItemId());
        JsonNode resp = apiClient.editItem(cookie, payload);
        if (!apiClient.isApiSuccess(resp)) {
            throw new BusinessException("更新闲鱼文案失败: " + resp.path("ret") + " body=" + resp);
        }
        product.setSyncStatus(Product.SYNC_OK);
        product.setLastSyncedAt(DateUtils.nowMillis());
        product.setUpdatedAt(DateUtils.nowMillis());
        productService.updateById(product);
        return product;
    }

    public void setShelf(Long accountId, Long productId, boolean onSale) {
        Product product = productService.getById(productId);
        if (product == null) {
            throw new BusinessException("商品不存在");
        }
        if (!StringUtils.hasText(product.getXianyuItemId())) {
            throw new BusinessException("商品未关联闲鱼 itemId");
        }
        String cookie = requireCookie(accountId != null ? accountId : product.getAccountId());
        JsonNode resp = onSale
                ? apiClient.upShelfItem(cookie, product.getXianyuItemId())
                : apiClient.downShelfItem(cookie, product.getXianyuItemId());
        if (!apiClient.isApiSuccess(resp)) {
            // 部分环境上下架 API 名不同：降级为仅改本地状态并提示
            log.warn("闲鱼上下架 API 返回非成功，仅更新本地: {}", resp.path("ret"));
        }
        product.setShelfStatus(onSale ? Product.SHELF_ON_SALE : Product.SHELF_OFF);
        product.setUpdatedAt(DateUtils.nowMillis());
        productService.updateById(product);
    }

    public Product copyLocal(Long productId) {
        Product src = productService.getById(productId);
        if (src == null) {
            throw new BusinessException("商品不存在");
        }
        Product copy = new Product();
        copy.setAccountId(src.getAccountId());
        copy.setName(src.getName() + " (副本)");
        copy.setTitle(src.getTitle());
        copy.setDescription(src.getDescription());
        copy.setPrice(src.getPrice());
        copy.setOriginalPrice(src.getOriginalPrice());
        copy.setStockQty(src.getStockQty());
        copy.setImagesJson(src.getImagesJson());
        copy.setCategoryId(src.getCategoryId());
        copy.setProvince(src.getProvince());
        copy.setCity(src.getCity());
        copy.setDeliveryContent(src.getDeliveryContent());
        copy.setAutoDelivery(src.getAutoDelivery());
        copy.setDefaultInventoryId(null);
        copy.setXianyuItemId(null);
        copy.setShelfStatus(Product.SHELF_OFF);
        copy.setSyncStatus(Product.SYNC_LOCAL);
        copy.setStatus(Product.STATUS_ENABLED);
        long now = DateUtils.nowMillis();
        copy.setCreatedAt(now);
        copy.setUpdatedAt(now);
        productService.save(copy);
        return copy;
    }

    /**
     * 一键搬家：将源账号商品详情拉取后，在目标账号重新发布
     */
    public Map<String, Object> migrateItems(Long fromAccountId, Long toAccountId, List<Long> productIds) {
        requireAccount(fromAccountId);
        requireAccount(toAccountId);
        String fromCookie = requireCookie(fromAccountId);
        String toCookie = requireCookie(toAccountId);

        int ok = 0;
        int fail = 0;
        List<String> messages = new ArrayList<>();
        for (Long pid : productIds) {
            try {
                Product src = productService.getById(pid);
                if (src == null || !StringUtils.hasText(src.getXianyuItemId())) {
                    fail++;
                    messages.add("跳过 " + pid + ": 无闲鱼ID");
                    continue;
                }
                JsonNode detail = apiClient.itemDetail(fromCookie, src.getXianyuItemId());
                Map<String, Object> publishData = buildPublishPayload(src, detail);
                JsonNode pubResp = apiClient.publishItem(toCookie, publishData);
                if (!apiClient.isApiSuccess(pubResp)) {
                    fail++;
                    messages.add(src.getXianyuItemId() + " 发布失败: " + pubResp.path("ret"));
                    continue;
                }
                String newItemId = extractPublishedItemId(pubResp);
                Product created = new Product();
                created.setAccountId(toAccountId);
                created.setName(StringUtils.hasText(src.getTitle()) ? src.getTitle() : src.getName());
                created.setTitle(src.getTitle());
                created.setDescription(src.getDescription());
                created.setPrice(src.getPrice());
                created.setImagesJson(src.getImagesJson());
                created.setCategoryId(src.getCategoryId());
                created.setDeliveryContent(src.getDeliveryContent());
                created.setAutoDelivery(src.getAutoDelivery());
                created.setXianyuItemId(newItemId);
                created.setShelfStatus(Product.SHELF_ON_SALE);
                created.setSyncStatus(Product.SYNC_OK);
                created.setStatus(Product.STATUS_ENABLED);
                long now = DateUtils.nowMillis();
                created.setCreatedAt(now);
                created.setUpdatedAt(now);
                created.setLastSyncedAt(now);
                productService.save(created);
                ok++;
                Thread.sleep(800 + (long) (Math.random() * 1200));
            } catch (Exception e) {
                fail++;
                messages.add("product " + pid + ": " + e.getMessage());
                log.warn("搬家失败 productId={}: {}", pid, e.getMessage());
            }
        }
        Map<String, Object> result = new HashMap<>();
        result.put("success", ok);
        result.put("failed", fail);
        result.put("messages", messages);
        return result;
    }

    public void refreshDetail(Long accountId, Long productId) {
        Product product = productService.getById(productId);
        if (product == null || !StringUtils.hasText(product.getXianyuItemId())) {
            throw new BusinessException("商品不存在或未关联闲鱼ID");
        }
        Long acc = accountId != null ? accountId : product.getAccountId();
        JsonNode detail = apiClient.itemDetail(requireCookie(acc), product.getXianyuItemId());
        applyDetailToProduct(product, detail);
        product.setLastSyncedAt(DateUtils.nowMillis());
        product.setSyncStatus(Product.SYNC_OK);
        product.setUpdatedAt(DateUtils.nowMillis());
        productService.updateById(product);
    }

    private Product upsertProductFromNode(Long accountId, JsonNode item) {
        JsonNode detailParams = item.path("detailParams");
        JsonNode priceInfo = item.path("priceInfo");
        JsonNode picInfo = item.path("picInfo");

        String itemId = firstText(
                text(item, "id", "itemId", "idleItemId"),
                text(detailParams, "itemId", "id"));
        if (!StringUtils.hasText(itemId)) {
            return null;
        }
        Product existing = productService.getOne(new LambdaQueryWrapper<Product>()
                .eq(Product::getAccountId, accountId)
                .eq(Product::getXianyuItemId, itemId)
                .last("LIMIT 1"));
        long now = DateUtils.nowMillis();
        if (existing == null) {
            existing = new Product();
            existing.setAccountId(accountId);
            existing.setXianyuItemId(itemId);
            existing.setCreatedAt(now);
            existing.setAutoDelivery(0);
            existing.setStatus(Product.STATUS_ENABLED);
        }
        String title = firstText(
                text(item, "title", "itemTitle", "name"),
                text(detailParams, "title"));
        if (StringUtils.hasText(title)) {
            existing.setTitle(title);
            existing.setName(title.length() > 200 ? title.substring(0, 200) : title);
        } else if (!StringUtils.hasText(existing.getName())) {
            existing.setName("闲鱼商品-" + itemId);
        }

        // 列表价在 priceInfo.price / detailParams.soldPrice，不是顶层 price
        BigDecimal price = firstDecimal(
                decimal(priceInfo, "price"),
                decimal(detailParams, "soldPrice", "price"),
                decimal(item, "soldPrice", "price", "itemPrice"),
                centToYuan(item, "priceInCent", "priceCent"),
                centToYuan(priceInfo, "priceInCent", "priceCent"));
        if (price != null) {
            existing.setPrice(price);
        }

        String img = firstText(
                text(picInfo, "picUrl", "url"),
                text(item, "picUrl", "pic", "mainPic"));
        if (StringUtils.hasText(img)) {
            existing.setImagesJson(JsonUtils.toJson(List.of(img)));
        }

        Integer stock = intVal(item, "quantity", "stock", "itemQuantity", "inventory");
        if (stock != null) {
            existing.setStockQty(stock);
        }

        String categoryId = firstText(
                text(detailParams, "categoryId"),
                text(item, "categoryId"));
        if (StringUtils.hasText(categoryId)) {
            existing.setCategoryId(categoryId);
        }

        String shelf = mapShelf(item);
        if (shelf != null) {
            existing.setShelfStatus(shelf);
        }
        existing.setSyncStatus(Product.SYNC_OK);
        existing.setLastSyncedAt(now);
        existing.setUpdatedAt(now);
        if (existing.getId() == null) {
            productService.save(existing);
        } else {
            productService.updateById(existing);
        }
        return existing;
    }

    private void applyDetailToProduct(Product product, JsonNode detail) {
        JsonNode data = detail.path("data");
        JsonNode item = data.has("itemDO") ? data.path("itemDO") : data;
        String title = text(item, "title", "itemTitle");
        if (StringUtils.hasText(title)) {
            product.setTitle(title);
            product.setName(title.length() > 200 ? title.substring(0, 200) : title);
        }
        String desc = text(item, "desc", "description", "itemDesc");
        if (StringUtils.hasText(desc)) {
            product.setDescription(desc);
        }
        BigDecimal price = firstDecimal(
                decimal(item, "soldPrice", "price", "itemPrice"),
                centToYuan(item, "priceInCent", "priceCent"));
        if (price == null) {
            JsonNode skuList = item.path("skuList");
            if (skuList.isArray() && !skuList.isEmpty()) {
                price = firstDecimal(
                        decimal(skuList.get(0), "price", "soldPrice"),
                        centToYuan(skuList.get(0), "priceInCent", "priceCent"));
            }
        }
        if (price != null) {
            product.setPrice(price);
        }
        BigDecimal original = decimal(item, "originalPrice");
        if (original != null) {
            product.setOriginalPrice(original);
        }

        Integer stock = sumSkuQuantity(item);
        if (stock == null) {
            stock = intVal(item, "quantity", "stock", "itemQuantity");
        }
        if (stock != null) {
            product.setStockQty(stock);
        }

        String shelf = mapShelf(item);
        if (shelf != null) {
            product.setShelfStatus(shelf);
        }

        List<String> images = extractDetailImages(item);
        if (!images.isEmpty()) {
            product.setImagesJson(JsonUtils.toJson(images));
        }
        String categoryId = text(item, "categoryId");
        if (StringUtils.hasText(categoryId)) {
            product.setCategoryId(categoryId);
        }
    }

    private Map<String, Object> buildPublishPayload(Product src, JsonNode detail) {
        // 搬家路径：精简载荷（保留原行为）
        Map<String, Object> data = new LinkedHashMap<>();
        String title = StringUtils.hasText(src.getTitle()) ? src.getTitle() : src.getName();
        String desc = StringUtils.hasText(src.getDescription()) ? src.getDescription() : title;
        Map<String, Object> itemText = new HashMap<>();
        itemText.put("title", title);
        itemText.put("desc", desc);
        itemText.put("titleDescSeparate", true);
        data.put("itemTextDTO", itemText);
        data.put("simpleItem", "true");
        data.put("itemTypeStr", "b");
        data.put("quantity", "1");
        data.put("sourceId", "pcMainPublish");
        data.put("bizcode", "pcMainPublish");
        data.put("publishScene", "pcMainPublish");
        Map<String, Object> priceDto = new HashMap<>();
        if (src.getPrice() != null) {
            priceDto.put("priceInCent",
                    String.valueOf(src.getPrice().multiply(BigDecimal.valueOf(100)).longValue()));
        }
        data.put("itemPriceDTO", priceDto);
        List<Map<String, Object>> images = new ArrayList<>();
        if (StringUtils.hasText(src.getImagesJson())) {
            try {
                List<?> list = JsonUtils.fromJson(src.getImagesJson(), List.class);
                if (list != null) {
                    boolean first = true;
                    for (Object o : list) {
                        images.add(toImageDo(o.toString(), 800, 800, first));
                        first = false;
                    }
                }
            } catch (Exception ignored) {
            }
        }
        data.put("imageInfoDOList", images);
        if (detail != null && detail.has("data")) {
            data.put("_sourceDetailHint", true);
        }
        return data;
    }

    private List<Map<String, Object>> preparePublishImages(String cookie, Product product) {
        List<Map<String, Object>> imageDos = new ArrayList<>();
        if (StringUtils.hasText(product.getImagesJson())) {
            List<?> supplied;
            try {
                supplied = JsonUtils.fromJson(product.getImagesJson(), List.class);
            } catch (Exception e) {
                throw new BusinessException("商品图片配置不是有效数组");
            }
            if (supplied != null && !supplied.isEmpty()) {
                if (supplied.size() > 9) throw new BusinessException("商品图片最多9张");
                List<String> uploadedUrls = new ArrayList<>();
                for (Object entry : supplied) {
                    String source = String.valueOf(entry);
                    String url = source;
                    int width = 800, height = 800;
                    if (source.startsWith("local-asset:")) {
                        try {
                            java.nio.file.Path asset = resolveLocalPublishAsset(publishAssetRoot(), source);
                            byte[] bytes = java.nio.file.Files.readAllBytes(asset);
                            java.awt.image.BufferedImage image = javax.imageio.ImageIO.read(
                                    new java.io.ByteArrayInputStream(bytes));
                            if (image == null) throw new java.io.IOException("不是可识别的图片");
                            width = image.getWidth();
                            height = image.getHeight();
                            String extension = asset.getFileName().toString().toLowerCase(java.util.Locale.ROOT).endsWith(".png") ? ".png" : ".jpg";
                            JsonNode result = apiClient.uploadImage(cookie, bytes,
                                    "product-" + product.getId() + "-" + imageDos.size() + extension);
                            url = result.path("url").asText("");
                        } catch (BusinessException e) {
                            throw e;
                        } catch (Exception e) {
                            throw new BusinessException("读取指定商品图片失败：" + e.getClass().getSimpleName(), e);
                        }
                    }
                    if (!url.startsWith("https://") && !url.startsWith("http://")) {
                        throw new BusinessException("商品图片必须是上传地址或允许目录内的 local-asset 图片");
                    }
                    imageDos.add(toImageDo(url, width, height, imageDos.isEmpty()));
                    uploadedUrls.add(url);
                }
                product.setImagesJson(JsonUtils.toJson(uploadedUrls));
                productService.updateById(product);
                return imageDos;
            }
        }
        if (isVideoServiceTitle(product.getTitle())) {
            throw new BusinessException("视频服务需提供真实选款图片，不能使用PDF资料封面");
        }
        // 优先重新上传一张本地封面，避免复用他人商品图被拒
        try {
            byte[] cover = renderCoverPng(StringUtils.hasText(product.getTitle())
                    ? product.getTitle() : product.getName());
            JsonNode uploaded = apiClient.uploadImage(cookie, cover, "cover-" + product.getId() + ".png");
            String url = uploaded.path("url").asText();
            int width = 800;
            int height = 800;
            String pix = uploaded.path("pix").asText("");
            if (pix.contains("x")) {
                String[] wh = pix.toLowerCase().split("x");
                width = Integer.parseInt(wh[0].trim());
                height = Integer.parseInt(wh[1].trim());
            }
            imageDos.add(toImageDo(url, width, height, true));
            product.setImagesJson(JsonUtils.toJson(List.of(url)));
            productService.updateById(product);
            return imageDos;
        } catch (Exception e) {
            log.warn("封面上传失败，尝试复用已有图片 URL: {}", e.getMessage());
        }
        if (StringUtils.hasText(product.getImagesJson())) {
            try {
                List<?> list = JsonUtils.fromJson(product.getImagesJson(), List.class);
                if (list != null) {
                    boolean first = true;
                    for (Object o : list) {
                        imageDos.add(toImageDo(o.toString(), 800, 800, first));
                        first = false;
                    }
                }
            } catch (Exception ignored) {
            }
        }
        if (imageDos.isEmpty()) {
            throw new BusinessException("发布需要至少一张商品图片");
        }
        return imageDos;
    }

    private static java.nio.file.Path publishAssetRoot() throws java.io.IOException {
        java.nio.file.Path directory = java.nio.file.Path.of("").toAbsolutePath();
        for (int i = 0; i < 6 && directory != null; i++, directory = directory.getParent()) {
            if (java.nio.file.Files.isRegularFile(directory.resolve("PROJECT_MAP.md"))) {
                return directory.resolve("outputs").toRealPath();
            }
        }
        throw new java.io.IOException("未找到项目输出目录");
    }

    static java.nio.file.Path resolveLocalPublishAsset(java.nio.file.Path root, String reference)
            throws java.io.IOException {
        if (!reference.startsWith("local-asset:")) throw new java.io.IOException("不是本地素材引用");
        java.nio.file.Path allowed = root.toRealPath();
        java.nio.file.Path asset = allowed.resolve(reference.substring("local-asset:".length())).normalize();
        if (!asset.startsWith(allowed)) throw new java.io.IOException("素材越过允许目录");
        asset = asset.toRealPath();
        if (!asset.startsWith(allowed) || !java.nio.file.Files.isRegularFile(asset)) {
            throw new java.io.IOException("素材不是允许目录内的文件");
        }
        String filename = asset.getFileName().toString().toLowerCase(java.util.Locale.ROOT);
        if (!(filename.endsWith(".png") || filename.endsWith(".jpg") || filename.endsWith(".jpeg"))
                || java.nio.file.Files.size(asset) > 10 * 1024 * 1024) {
            throw new java.io.IOException("仅支持10MB以内的PNG或JPEG");
        }
        return asset;
    }

    static boolean isWebsiteServiceTitle(String title) {
        return title != null && title.matches(".*(官网定制|官网制作|网站制作|网站建设|展示网站|企业官网).*");
    }

    private static boolean isDocumentCategory(Map<String, Object> category) {
        if (category == null) return false;
        String name = String.valueOf(category.getOrDefault("catName", ""));
        return name.matches(".*(资料|素材|源文件|电子书|教程|论文|文档).*");
    }

    static boolean isVideoServiceTitle(String title) {
        return title != null && title.matches(".*(模板视频|视频制作|视频定制|拍摄剪辑|视频剪辑).*")
                && !title.matches(".*(学习资料|电子书|教程|笔记).*");
    }

    static boolean isVideoServiceCategory(Map<String, Object> category) {
        if (category == null) return false;
        String name = String.valueOf(category.getOrDefault("catName", ""));
        return name.matches(".*(视频|剪辑|摄影|摄像|拍摄|动画设计|设计服务|技能服务).*")
                && !name.matches(".*(资料|素材|源文件|教程|电子书).*");
    }

    private Map<String, Object> buildFullPublishPayload(String cookie, Product src,
                                                        List<Map<String, Object>> imageDos) {
        String title = StringUtils.hasText(src.getTitle()) ? src.getTitle() : src.getName();
        String desc = StringUtils.hasText(src.getDescription()) ? src.getDescription() : title;
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("freebies", false);
        data.put("itemTypeStr", "b");
        data.put("quantity", "1");
        data.put("simpleItem", "true");
        data.put("imageInfoDOList", imageDos);
        Map<String, Object> itemText = new HashMap<>();
        itemText.put("title", title);
        itemText.put("desc", desc);
        itemText.put("titleDescSeparate", true);
        data.put("itemTextDTO", itemText);
        data.put("itemLabelExtList", new ArrayList<>());
        Map<String, Object> priceDto = new HashMap<>();
        boolean defaultPrice = src.getPrice() == null || src.getPrice().compareTo(BigDecimal.ZERO) <= 0;
        if (!defaultPrice) {
            priceDto.put("priceInCent",
                    String.valueOf(src.getPrice().multiply(BigDecimal.valueOf(100)).longValue()));
        }
        data.put("itemPriceDTO", priceDto);
        data.put("defaultPrice", defaultPrice);
        data.put("userRightsProtocols", List.of(Map.of(
                "enable", false,
                "serviceCode", "SKILL_PLAY_NO_MIND")));
        // 电子资料：包邮
        Map<String, Object> postFee = new HashMap<>();
        postFee.put("canFreeShipping", true);
        postFee.put("supportFreight", true);
        postFee.put("onlyTakeSelf", false);
        data.put("itemPostFeeDTO", postFee);
        data.put("itemAddrDTO", resolvePublishAddress(cookie));
        data.put("itemCatDTO", resolvePublishCategory(cookie, title, desc, imageDos, src.getCategoryId()));
        data.put("uniqueCode", String.valueOf(System.currentTimeMillis()) + "001");
        data.put("sourceId", "pcMainPublish");
        data.put("bizcode", "pcMainPublish");
        data.put("publishScene", "pcMainPublish");
        return data;
    }

    private Map<String, Object> resolvePublishAddress(String cookie) {
        try {
            JsonNode poi = apiClient.getLocalPoi(cookie, 116.397128, 39.916527);
            JsonNode addresses = poi.path("data").path("commonAddresses");
            if (addresses.isArray() && !addresses.isEmpty()) {
                JsonNode loc = addresses.get(0);
                Map<String, Object> addr = new LinkedHashMap<>();
                addr.put("area", text(loc, "area"));
                addr.put("city", text(loc, "city"));
                addr.put("divisionId", text(loc, "divisionId"));
                addr.put("gps", loc.path("longitude").asText() + "," + loc.path("latitude").asText());
                addr.put("poiId", text(loc, "poiId"));
                addr.put("poiName", firstText(text(loc, "poi"), text(loc, "poiName")));
                addr.put("prov", text(loc, "prov"));
                return addr;
            }
        } catch (Exception e) {
            log.warn("获取发布地址失败，使用兜底: {}", e.getMessage());
        }
        Map<String, Object> fallback = new LinkedHashMap<>();
        fallback.put("area", "东城区");
        fallback.put("city", "北京");
        fallback.put("divisionId", "110101");
        fallback.put("gps", "116.397128,39.916527");
        fallback.put("poiName", "北京市");
        fallback.put("prov", "北京");
        return fallback;
    }

    private Map<String, Object> resolvePublishCategory(String cookie, String title, String desc,
                                                       List<Map<String, Object>> imageDos,
                                                       String fallbackCatId) {
        // 发布必须带 channelCatId，否则闲鱼返回 FAIL_BIZ_CHANNEL_CAT_ID_PATH_QUERY_ERROR
        Map<String, Object> recommended = tryRecommendCategory(cookie, title, desc, imageDos);
        if (isVideoServiceTitle(title)) {
            if (isVideoServiceCategory(recommended)) return recommended;
            recommended = tryRecommendCategory(cookie, "视频剪辑制作服务", "视频制作与剪辑服务，按客户内容制作成片", imageDos);
            if (isVideoServiceCategory(recommended)) return recommended;
            throw new BusinessException("未取得视频制作服务类目，已停止发布，不回退到PDF资料类目");
        }
        if (isWebsiteServiceTitle(title)) {
            if (recommended != null && !isDocumentCategory(recommended)) {
                return recommended;
            }
            recommended = tryRecommendCategory(cookie, "网站建设定制服务", "企业展示网站制作与改版，按需求确认范围", imageDos);
            if (recommended != null && !isDocumentCategory(recommended)) {
                return recommended;
            }
            throw new BusinessException("未取得网站建设服务类目，已停止发布，不回退到资料类目");
        }
        if (recommended != null) {
            return recommended;
        }
        recommended = tryRecommendCategory(cookie, "PDF电子书学习资料", "电子资料 PDF 学习教程", imageDos);
        if (recommended != null) {
            return recommended;
        }
        Map<String, Object> cat = new LinkedHashMap<>();
        cat.put("catId", StringUtils.hasText(fallbackCatId) ? fallbackCatId : "50023914");
        cat.put("catName", "资料素材/源文件");
        cat.put("channelCatId", "201454708");
        cat.put("tbCatId", "201160807");
        return cat;
    }

    private Map<String, Object> tryRecommendCategory(String cookie, String title, String desc,
                                                    List<Map<String, Object>> imageDos) {
        try {
            JsonNode resp = apiClient.recommendCategory(cookie, title, desc, imageDos);
            JsonNode predict = resp.path("data").path("categoryPredictResult");
            String catId = predict.path("catId").asText("");
            String channelCatId = predict.path("channelCatId").asText("");
            if (StringUtils.hasText(catId) && StringUtils.hasText(channelCatId)) {
                Map<String, Object> cat = new LinkedHashMap<>();
                cat.put("catId", catId);
                cat.put("catName", predict.path("catName").asText(""));
                cat.put("channelCatId", channelCatId);
                String tbCatId = predict.path("tbCatId").asText("");
                if (StringUtils.hasText(tbCatId)) {
                    cat.put("tbCatId", tbCatId);
                }
                return cat;
            }
            log.warn("类目推荐缺少 channelCatId title={} predict={}", title, predict);
        } catch (Exception e) {
            log.warn("类目推荐失败 title={}: {}", title, e.getMessage());
        }
        return null;
    }

    private static Map<String, Object> toImageDo(String url, int width, int height, boolean major) {
        Map<String, Object> img = new LinkedHashMap<>();
        Map<String, Object> extra = new LinkedHashMap<>();
        extra.put("isH", "false");
        extra.put("isT", "false");
        extra.put("raw", "false");
        img.put("extraInfo", extra);
        img.put("isQrCode", false);
        img.put("url", url);
        img.put("heightSize", height);
        img.put("widthSize", width);
        img.put("major", major);
        img.put("type", 0);
        img.put("status", "done");
        return img;
    }

    private static byte[] renderCoverPng(String title) throws Exception {
        int w = 800;
        int h = 800;
        java.awt.image.BufferedImage image =
                new java.awt.image.BufferedImage(w, h, java.awt.image.BufferedImage.TYPE_INT_RGB);
        java.awt.Graphics2D g = image.createGraphics();
        g.setRenderingHint(java.awt.RenderingHints.KEY_ANTIALIASING,
                java.awt.RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new java.awt.Color(24, 90, 160));
        g.fillRect(0, 0, w, h);
        g.setColor(java.awt.Color.WHITE);
        g.setFont(new java.awt.Font("SansSerif", java.awt.Font.BOLD, 36));
        String text = title == null ? "PDF" : title;
        if (text.length() > 18) {
            text = text.substring(0, 18) + "...";
        }
        java.awt.FontMetrics fm = g.getFontMetrics();
        int x = Math.max(40, (w - fm.stringWidth(text)) / 2);
        int y = h / 2;
        g.drawString(text, x, y);
        g.setFont(new java.awt.Font("SansSerif", java.awt.Font.PLAIN, 28));
        g.drawString("PDF Learning Material", 200, y + 60);
        g.dispose();
        java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
        javax.imageio.ImageIO.write(image, "png", baos);
        return baos.toByteArray();
    }

    private String extractPublishedItemId(JsonNode pubResp) {
        JsonNode data = pubResp.path("data");
        String id = text(data, "itemId", "idleItemId", "id");
        if (StringUtils.hasText(id)) return id;
        return text(data.path("item"), "itemId", "id");
    }

    private List<JsonNode> extractItemNodes(JsonNode resp) {
        List<JsonNode> list = new ArrayList<>();
        JsonNode data = resp.path("data");
        JsonNode cardList = data.path("cardList");
        if (cardList.isArray()) {
            for (JsonNode c : cardList) {
                JsonNode item = c.path("cardData");
                if (item.isMissingNode()) item = c.path("item");
                if (item.isMissingNode()) item = c;
                list.add(item);
            }
            return list;
        }
        JsonNode items = data.path("items");
        if (items.isArray()) {
            items.forEach(list::add);
            return list;
        }
        JsonNode itemList = data.path("itemList");
        if (itemList.isArray()) {
            itemList.forEach(list::add);
        }
        return list;
    }

    /**
     * 闲鱼 itemStatus：0=在售；非 0（已售/下架等）视为下架。
     * 旧逻辑把 "0" 当成下架，导致同步后几乎全是「下架」。
     */
    private String mapShelf(JsonNode item) {
        JsonNode statusNode = item.get("itemStatus");
        if (statusNode != null && !statusNode.isNull()) {
            if (statusNode.isNumber()) {
                return statusNode.asInt() == 0 ? Product.SHELF_ON_SALE : Product.SHELF_OFF;
            }
            String raw = statusNode.asText("").trim();
            if ("0".equals(raw)) {
                return Product.SHELF_ON_SALE;
            }
            if (!raw.isEmpty()) {
                try {
                    return Integer.parseInt(raw) == 0 ? Product.SHELF_ON_SALE : Product.SHELF_OFF;
                } catch (NumberFormatException ignored) {
                    // fall through
                }
            }
        }
        String s = text(item, "status", "shelfStatus", "itemStatusStr");
        if (s == null) {
            return Product.SHELF_ON_SALE;
        }
        String lower = s.toLowerCase();
        if (lower.contains("down") || lower.contains("off") || lower.contains("sold")
                || lower.contains("删除") || lower.contains("下架") || lower.contains("已售")) {
            return Product.SHELF_OFF;
        }
        if (lower.contains("sale") || lower.contains("在售") || "1".equals(s)) {
            return Product.SHELF_ON_SALE;
        }
        return Product.SHELF_ON_SALE;
    }

    private static Integer sumSkuQuantity(JsonNode item) {
        JsonNode skuList = item.path("skuList");
        if (!skuList.isArray() || skuList.isEmpty()) {
            return null;
        }
        int sum = 0;
        boolean any = false;
        for (JsonNode sku : skuList) {
            Integer q = intVal(sku, "quantity", "stock", "itemQuantity");
            if (q != null) {
                sum += q;
                any = true;
            }
        }
        return any ? sum : null;
    }

    private static List<String> extractDetailImages(JsonNode item) {
        List<String> images = new ArrayList<>();
        JsonNode imageInfos = item.path("imageInfos");
        if (imageInfos.isArray()) {
            for (JsonNode img : imageInfos) {
                String url = text(img, "url", "picUrl");
                if (StringUtils.hasText(url)) {
                    images.add(url);
                }
            }
        }
        if (images.isEmpty()) {
            String single = text(item.path("picInfo"), "picUrl", "url");
            if (StringUtils.hasText(single)) {
                images.add(single);
            }
        }
        return images;
    }

    private static String firstText(String... values) {
        if (values == null) return null;
        for (String v : values) {
            if (StringUtils.hasText(v)) return v;
        }
        return null;
    }

    private static BigDecimal firstDecimal(BigDecimal... values) {
        if (values == null) return null;
        for (BigDecimal v : values) {
            if (v != null) return v;
        }
        return null;
    }

    private static BigDecimal centToYuan(JsonNode node, String... keys) {
        if (node == null || node.isMissingNode()) return null;
        for (String k : keys) {
            JsonNode n = node.get(k);
            if (n == null || n.isNull()) continue;
            try {
                long cent = n.isNumber() ? n.asLong() : Long.parseLong(n.asText().trim());
                return BigDecimal.valueOf(cent).movePointLeft(2);
            } catch (Exception ignored) {
            }
        }
        return null;
    }

    private static Integer intVal(JsonNode node, String... keys) {
        if (node == null || node.isMissingNode()) return null;
        for (String k : keys) {
            JsonNode n = node.get(k);
            if (n == null || n.isNull()) continue;
            try {
                if (n.isNumber()) return n.asInt();
                String t = n.asText("").trim();
                if (!t.isEmpty()) return Integer.parseInt(t);
            } catch (Exception ignored) {
            }
        }
        return null;
    }

    private Account requireAccount(Long accountId) {
        Account a = accountService.getById(accountId);
        if (a == null) throw new BusinessException("账号不存在");
        return a;
    }

    private String requireCookie(Long accountId) {
        String cookie = cookieManager.getCookie(accountId);
        if (!StringUtils.hasText(cookie)) {
            throw new BusinessException("Cookie 为空，请重新录入");
        }
        return cookie;
    }

    private static String text(JsonNode node, String... keys) {
        if (node == null || node.isMissingNode()) return null;
        for (String k : keys) {
            JsonNode n = node.get(k);
            if (n != null && !n.isNull() && StringUtils.hasText(n.asText())) {
                return n.asText();
            }
        }
        return null;
    }

    private static BigDecimal decimal(JsonNode node, String... keys) {
        String t = text(node, keys);
        if (!StringUtils.hasText(t)) return null;
        try {
            return new BigDecimal(t.replace("¥", "").trim());
        } catch (Exception e) {
            return null;
        }
    }
}
