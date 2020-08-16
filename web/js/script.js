$(function() {
	asynccontext = async function(){
		rootpath = await eel.get_root()()
		var browse = $('#browser').browse({
			root: rootpath,
			separator: '/',
			contextmenu: true,
			dir: function(path) {
				return(eel.get_path_infos(path)());
			},
			open: function(filename) {
				console.log('opening ' + filename);
			}
		});
	};
	asynccontext();
});