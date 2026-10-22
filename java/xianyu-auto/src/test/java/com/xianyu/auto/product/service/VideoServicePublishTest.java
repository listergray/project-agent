package com.xianyu.auto.product.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.xianyu.client.XianyuApiClient;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.test.util.ReflectionTestUtils;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class VideoServicePublishTest {
    @TempDir Path root;

    @Test void localImagesStayInsideOutputDirectory() throws Exception {
        Path cover = Files.write(root.resolve("cover.png"), new byte[]{1});
        assertEquals(cover.toRealPath(), XianyuItemService.resolveLocalPublishAsset(root, "local-asset:cover.png"));
        assertThrows(java.io.IOException.class,
                () -> XianyuItemService.resolveLocalPublishAsset(root, "local-asset:../private.png"));
        Files.write(root.resolve("secret.env"), new byte[]{1});
        assertThrows(java.io.IOException.class,
                () -> XianyuItemService.resolveLocalPublishAsset(root, "local-asset:secret.env"));
    }

    @Test void videoServicesAreDistinctFromLearningMaterial() {
        assertTrue(XianyuItemService.isVideoServiceTitle("模板视频制作50–60秒10条5元"));
        assertFalse(XianyuItemService.isVideoServiceTitle("视频剪辑学习资料"));
        assertTrue(XianyuItemService.isVideoServiceCategory(Map.of("catName", "视频剪辑/制作")));
        assertFalse(XianyuItemService.isVideoServiceCategory(Map.of("catName", "视频素材/源文件")));
    }

    @Test void serviceCategoryFailureCannotFallBackToPdf() throws Exception {
        XianyuApiClient api = mock(XianyuApiClient.class);
        when(api.recommendCategory(anyString(), anyString(), anyString(), anyList()))
                .thenReturn(new ObjectMapper().readTree("{\"data\":{\"categoryPredictResult\":{\"catId\":\"1\",\"channelCatId\":\"2\",\"catName\":\"资料素材/源文件\"}}}"));
        XianyuItemService service = new XianyuItemService(null, null, null, api);
        assertThrows(BusinessException.class, () -> ReflectionTestUtils.invokeMethod(service,
                "resolvePublishCategory", "cookie", "模板视频制作", "成片服务", List.of(), null));
        verify(api, never()).recommendCategory(anyString(), eq("PDF电子书学习资料"), anyString(), anyList());
    }

    @Test void matchingServiceCategoryIsPreserved() throws Exception {
        XianyuApiClient api = mock(XianyuApiClient.class);
        when(api.recommendCategory(anyString(), anyString(), anyString(), anyList()))
                .thenReturn(new ObjectMapper().readTree("{\"data\":{\"categoryPredictResult\":{\"catId\":\"11\",\"channelCatId\":\"22\",\"catName\":\"视频剪辑/制作\"}}}"));
        XianyuItemService service = new XianyuItemService(null, null, null, api);
        Map<?, ?> result = ReflectionTestUtils.invokeMethod(service,
                "resolvePublishCategory", "cookie", "模板视频制作", "成片服务", List.of(), null);
        assertNotNull(result);
        assertEquals("11", result.get("catId"));
    }
}
