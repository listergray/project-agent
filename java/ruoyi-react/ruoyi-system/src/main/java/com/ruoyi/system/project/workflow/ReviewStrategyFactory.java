package com.ruoyi.system.project.workflow;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;
import com.ruoyi.common.exception.ServiceException;

/**
 * ??????
 */
@Component
public class ReviewStrategyFactory
{
    private final Map<String, ReviewStrategy> strategies = new HashMap<>();

    public ReviewStrategyFactory(List<ReviewStrategy> list)
    {
        for (ReviewStrategy s : list)
        {
            strategies.put(s.stage(), s);
        }
    }

    public ReviewStrategy get(String stage)
    {
        ReviewStrategy strategy = strategies.get(stage);
        if (strategy == null)
        {
            throw new ServiceException("unknown review stage: " + stage);
        }
        return strategy;
    }
}
