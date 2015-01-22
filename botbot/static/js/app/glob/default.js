$$.Views.Glob = Backbone.View.extend({

    initialize: function (options) {
        log('Glob:initialize');
        // options
        this.eventSourceUrl = options.source;
        var width = options.width || 960;
        var height = options.height || 550;

        this.configureMap(width, height);
        this.activateMap();

        this.setupEventSource();
    },

    configureMap: function(width, height){
        this.svg = d3.select(this.el).append("svg")
            .attr("width", width)
            .attr("height", height);
        this.svg.map = this.svg.append("g").attr('class', 'map');
        this.svg.circles = this.svg.append("g").attr('class', 'map');
        this.projection = d3.geo.mercator()
            .center([0, 33 ])
            .scale(150)
            .rotate([-10,0]);
    },

    setupEventSource: function () {
        log('Glob:setupEventSource');
        var self = this;
        if (this.source) {
            return;
        }
        log('Creating event source');
        this.source = new EventSource(this.eventSourceUrl);

        var g = this.svg.circles;
        var projection = this.projection;

        this.source.addEventListener('loc', function (e) {
            //log('received');
            log(JSON.parse(e.data));
            //log(this);
            //log('end');
            g.data([JSON.parse(e.data)])
                .append("circle")
                .attr("cx", function(d) {
                    return projection([d[1], d[0]])[0];
                })
                .attr("cy", function(d) {
                    return projection([d[1], d[0]])[1];
                })
                .style("fill", "lime")
                .attr("r", 0)
                .transition()
                .duration(100)
                .attr("r", 4)
                .transition()
                .delay(100)
                .attr("r", 12)
                .style("opacity", 0)
                .duration(500)
                .remove();

        }, false);
    },

    activateMap: function(){

        var path = d3.geo.path()
            .projection(this.projection);

        var g = this.svg.map;

        // load and display the World
        d3.json("/static/data/world-110m2.json", function(error, topology) {
            x = topology
            g.selectAll("path")
                .data(topojson.feature(topology, topology.objects.countries)
                      .features)
                .enter()
                .append("path")
                .attr("d", path)
        });

        var projection = this.projection;
        var zoom = d3.behavior.zoom()
            .on("zoom",function() {
                d3.selectAll('g.map')
                    .attr("transform","translate("+
                          d3.event.translate.join(",")+")scale("+d3.event.scale+")");
                g.selectAll("circle")
                    .attr("d", path.projection(projection));
                g.selectAll("path")
                    .attr("d", path.projection(projection));
            });

        this.svg.call(zoom);
    }

});

$(document).ready(function () {
    v = new $$.Views.Glob({
        el: $('#Glob'),
        source: $('#Glob').data('source')
    })
})
