$(document).ready(function(){
    var doc = new Doc();
    doc.render();
});

function Doc(){
    this.indent_size = 30; // pixels
    this.current_indent = 0;
    this.data =
        {
            'hello':55,
            'world':{'num':66, 'string': 'Sameple Styring'},
            'LiST':[55,66,88]
        }
}

Doc.prototype.render = function(dat, node){
    // when nothing has been passed in, bootstrap by running recursive
    // render on this data
    if(typeof(dat)==='undefined'){
        this.render(this.data, $("#render"));
    }

    else if (typeof(dat)==='object'){
        this.render_object(dat, node);
    }
    else if (typeof(dat)==='number'){
        this.render_dom(dat, node);
    }
}

Doc.prototype.render_dom = function(text, node){
    new_node = $("<div>").text(text);
    new_node.css("margin-left", this.current_indent);
    node.append(new_node);
}

Doc.prototype.indent = function(){
    this.current_indent += this.indent_size;
}

Doc.prototype.dedent = function(){
    this.current_indent -= this.indent_size;
}

Doc.prototype.render_object = function(dat, node){
    if(Object.prototype.toString.call(dat) === '[object Array]'){
        this.render_dom("[", node)
        this.indent();
        for(var item in dat){
            this.render_dom(item +',', node);
        }
        this.dedent();
        this.render_dom("]", node);
    }
    else{
        this.render_dom("{", node)
        this.indent();
        for(var key in dat){
            var value = dat[key];
            this.render_pair(key, value, node);
        }
        this.dedent();
        this.render_dom("}", node);
    }
}

Doc.prototype.render_pair = function(key, value, node){
    if (typeof(value)==='object'){
        this.render_dom(key + ":", node);
        var value_node = $("<div>");
        node.append(value_node);
        this.render_object(value, value_node);
    }
    else{
        this.render_dom(key + " : " + value, node);
    };
}


